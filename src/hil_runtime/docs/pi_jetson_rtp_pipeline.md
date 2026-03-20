# Pi to Jetson RTP HIL Pipeline

## Scope

This document describes the current verified HDMI -> RTP -> TensorRT path for the Pi 5 and Jetson Nano checked on `2026-03-19`.

All host / Pi / Jetson runtime helpers referenced here now live under the top-level `src/hil_runtime/` tree. The platform product code remains in `src/carla_web_platform/`.

The primary path is now:

1. Raspberry Pi 5 captures HDMI from `/dev/video0`
2. Pi encodes H.264 and sends RTP over the direct Ethernet link from `eth0`
3. Jetson Nano receives the RTP stream on `udp://0.0.0.0:5000`
4. The single-process C++ detector handles RTP ingest, `nvv4l2decoder`, TensorRT inference, and local box overlay display
5. Optional result reporting posts metrics back to the Pi receiver at `http://192.168.50.1:18765/dut-results`

Older `USB ECM / 192.168.7.x` notes were removed here on purpose because they do not describe the currently verified wiring.

## Verified Network Topology

- Pi `eth0`: `192.168.50.1/24`
- Jetson `eth0`: `192.168.50.2/24`
- Pi target RTP endpoint: `192.168.50.2:5000`
- Pi DUT result receiver: `http://192.168.50.1:18765/dut-results`

Important runtime note:

- If Jetson also uses Wi-Fi for internet access, do not leave the `eth0` default gateway pointing at `192.168.50.1`. Keep the direct link as a local `/24` route only.

## Pi Side

### Prerequisites

- HDMI capture input is available as `/dev/video0`
- Pi `eth0` is configured as `192.168.50.1/24`
- GStreamer CLI and plugins are installed on the Pi
- `v4l2-ctl` is available for diagnostics

Recommended packages on Raspberry Pi OS:

```bash
sudo apt update
sudo apt install -y \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  v4l-utils
```

### Capture Format That Actually Works

The tc358743 HDMI bridge on the verified Pi was locked to `1920x1080p60`. The working `/dev/video0` format was:

```bash
v4l2-ctl -d /dev/video0 --set-fmt-video=width=1920,height=1080,pixelformat=RGB3
v4l2-ctl -d /dev/video0 --get-fmt-video
```

Expected result:

```text
Width/Height : 1920/1080
Pixel Format : 'RGB3'
```

`RGB4` and ad hoc `1280x720` requests were misleading on this hardware path and caused allocation or format mismatch failures.

### Start RTP Streaming

The Pi launch script now defaults to the verified direct-link layout and the 1080p30 injection target:

```bash
cd /path/to/duckPark/src
bash hil_runtime/pi/scripts/start_pi_hdmi_rtp_stream.sh
```

Current defaults in that script:

- target host: `192.168.50.2`
- target port: `5000`
- source width and height: `1920x1080`
- output framerate after `videorate`: `30`
- direct-link diagnostics interface: `eth0`
- forced V4L2 input pixel format before launch: `RGB3`

Useful overrides:

```bash
PI_HDMI_RTP_TARGET_HOST=192.168.50.2 \
PI_HDMI_RTP_WIDTH=1920 \
PI_HDMI_RTP_HEIGHT=1080 \
PI_HDMI_RTP_FRAMERATE=30 \
PI_HDMI_RTP_BITRATE_KBPS=8000 \
bash hil_runtime/pi/scripts/start_pi_hdmi_rtp_stream.sh
```

Notes from the verified Pi:

- `v4l2h264enc` was not available on the checked image
- the working path therefore used `x264enc`
- the script now keeps `x264enc` in zerolatency mode, avoids B-frames, and uses a GOP closer to the requested frame rate instead of forcing all-I frames

If the DUT result receiver is not already running on port `18765`, start it with:

```bash
cd /path/to/duckPark/src
PI_GATEWAY_DUT_RESULT_RECEIVER_PORT=18765 \
bash hil_runtime/pi/scripts/start_pi_dut_result_receiver.sh
```

## Jetson Side

### Current Primary Runtime

The current primary runtime is the non-ROS C++ detector:

- binary: `/home/wheeltec/duckpark_cpp_detector/build/duckpark_cpp_detector`
- engine: `/home/wheeltec/yolo_ros2/module/yolov4-tiny.engine`
- labels: `/home/wheeltec/yolo_ros2/module/coco.names`
- decoder: `nvv4l2decoder`

To start the live detector path:

```bash
cd /path/to/duckPark/src
JETSON_CPP_DETECTOR_DISPLAY=1 \
JETSON_CPP_DETECTOR_SOURCE='udp://0.0.0.0:5000' \
bash hil_runtime/jetson/scripts/start_jetson_cpp_detector.sh
```

If metrics need to be posted back to the Pi result receiver, wrap the detector with:

```bash
cd /path/to/duckPark/src
JETSON_CPP_DETECTOR_DISPLAY=1 \
JETSON_CPP_DETECTOR_SOURCE='udp://0.0.0.0:5000' \
JETSON_CPP_DETECTOR_WRAP_NON_ROS_DEMO=1 \
JETSON_RESULT_URL='http://192.168.50.1:18765/dut-results' \
bash hil_runtime/jetson/scripts/start_jetson_cpp_detector.sh
```

### Legacy ROS2 Path

The ROS2 `jetson_rtp_camera_node -> tensorrt_yolo` path still exists in the repo, but it is not the primary verified path for this document. If you use it, make sure the result URL also points at `http://192.168.50.1:18765/dut-results`.

## Verified Live Smoke on 2026-03-19

What was proven live on hardware:

- Pi capture source: `tc358743` reporting `1920x1080p60`
- Pi `/dev/video0` fixed to `RGB3 1920x1080`
- Pi -> Jetson direct Ethernet link: working on `192.168.50.1/24` to `192.168.50.2/24`
- Jetson C++ detector received RTP, used `nvv4l2decoder`, ran TensorRT inference, and displayed boxes on screen

Proven end-to-end baseline run:

- Pi sender profile: `1920x1080 RGB` input, downscaled to `960x540@15` before `x264enc`
- Jetson result: `processed_frames=30`
- detection count: `159`
- average latency: `57.555 ms`
- output fps: `13.945`

That baseline was used to prove the live path before pushing the injection target higher.

Current 1080p30 live result:

- Pi `gst-launch -v` negotiated `1920x1080@30` end-to-end on the sender path and the RTP payload advertised `a-framerate=(string)30`
- Jetson consumed the 1080p30 stream and completed `processed_frames=45`
- Jetson metrics for that run: `avg_latency_ms=58.858`, `output_fps=11.039`, `frame_width=1920`, `frame_height=1080`
- The same run recorded `detection_count=0`, so the transport and inference path were live, but the specific captured scene did not produce COCO detections at the current threshold

Current optimization focus:

- Keep the Pi injection path at `1920x1080@30`
- Raise Jetson-side effective inference throughput above the current `~11 fps`
- The same `1920x1080@30` stream reached `output_fps=16.721` and `avg_latency_ms=55.365` when the detector was rerun with `--no-display`, so local display is a meaningful part of the current bottleneck

## Investigation Log on 2026-03-20

This section records the real problems hit during the next live validation pass, how they were narrowed down, and what changed as a result.

### Problem 1: Pi Was Capturing the Wrong Desktop

Observed behavior:

- opening a browser image on the Ubuntu host did not show up on the Pi capture
- Pi only saw a desktop background or a different workspace
- `tc358743` sometimes reported `TMDS signal detected: no` even though the cable was connected

How it was investigated:

- on the Pi, `v4l2-ctl -d /dev/v4l-subdev2 --log-status` was used to confirm whether HDMI sync was actually present
- on the Ubuntu host, `xrandr --query` showed that `DP-0` was the active display while `HDMI-0` was connected but not mirroring the main desktop
- a Pi-side snapshot was then captured from `/dev/video0` to confirm what the Pi was really seeing

Resolution:

- the host display was changed so `HDMI-0` mirrors `DP-0`
- a working runtime command was:

```bash
DISPLAY=:1 XAUTHORITY=/home/du/.Xauthority \
xrandr --output HDMI-0 --mode 1920x1080 --rate 60 --same-as DP-0
```

Result:

- after the mirror change, the Pi snapshot showed the CARLA render window correctly
- this problem is considered solved for the current host wiring

### Problem 2: Jetson Display Colors Were Red/Blue Swapped

Observed behavior:

- the Jetson detector window showed the incoming scene with red and blue swapped

How it was investigated:

- Pi-side conversion was rejected as the preferred fix because the Pi was already paying for `RGB -> I420` before `x264enc`
- the existing ROS2 fallback node already had a `swap_rb` option, so the same control was added to the C++ detector path

Resolution:

- `--swap-rb` was added to the C++ detector
- `JETSON_CPP_DETECTOR_SWAP_RB=1` was added to the Jetson launch wrapper path

Result:

- color correction was verified once on the Jetson display path
- this problem is considered solved in the current local repo and was synced once to the checked Jetson during validation

### Problem 3: Jetson Showed Partial or Striped Frames at 1080p30

Observed behavior:

- the Jetson detector window showed only the upper part of the frame correctly
- lower regions appeared dark, gray, or vertically striped
- the log repeatedly emitted `gst_buffer_resize_range` warnings

How it was investigated:

1. The detector was rerun with and without `swap_rb`.
   Result: corruption remained, so the color swap was not the root cause.
2. TensorRT inference was isolated out of the loop by using a pure `cv2.VideoCapture(...)` receiver on Jetson and saving a single frame.
   Result: the saved frame was still corrupted, so the fault was upstream of `yolo::Net.detect(...)`.
3. Multiple receiver pipelines were compared against the same live Pi stream.

Receiver pipeline findings:

- `hw_bgrx` without RTP jitter handling: corrupted
- `sw_avdec` without RTP jitter handling: incomplete or gray lower frame
- `hw_i420` without RTP jitter handling: corrupted
- `hw_double` without RTP jitter handling: corrupted
- `sw_base` with only the current basic UDP front-end: incomplete
- `sw_buf` with a larger UDP socket buffer only: still incomplete
- `sw_jitter` with `udpsrc buffer-size=4194304 ! rtpjitterbuffer latency=50 drop-on-latency=true`: full frame captured correctly
- `hw_jitter` with the same RTP front-end plus `nvv4l2decoder`: full frame captured correctly on the isolated first-frame test

Current conclusion:

- the 1080p30 failure is not caused by the TensorRT model and not caused by `swap_rb`
- the decisive improvement came from the RTP receive front-end, specifically adding:
  - a larger `udpsrc` socket buffer
  - `rtpjitterbuffer latency=50 drop-on-latency=true`
- the current best working receive pattern is:

```text
udpsrc address=0.0.0.0 port=5000 buffer-size=4194304 caps="application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96"
! rtpjitterbuffer latency=50 drop-on-latency=true
! rtph264depay
! h264parse
! nvv4l2decoder enable-max-performance=1
! nvvidconv
! video/x-raw,format=BGRx
! videoconvert
! video/x-raw,format=BGR
! appsink drop=true max-buffers=1 sync=false
```

Resolution status:

- this receive-front-end fix was first validated in isolated OpenCV capture tests for both software decode and hardware decode
- it was then rechecked on `2026-03-20` through the full C++ detector path after rebuilding and syncing the latest source
- full detector retest result:
  - `processed_frames=132`
  - `detection_count=1320`
  - `avg_latency_ms=55.494`
  - `output_fps=9.477`
  - `frame_width=1920`
  - `frame_height=1080`
- the Jetson detector window showed a complete frame with correct colors and visible detection boxes during that retest
- residual issue: `gst_buffer_resize_range` warnings still appeared in the detector log even though the displayed frame and detections were functionally correct

### Problem 4: Jetson Time Was Wrong

Observed behavior:

- metrics and logs written during March 2026 validation were stamped with March 2025 timestamps
- the build also emitted clock-skew warnings

How it was investigated:

- the wrong year appeared directly in metrics JSON and build output during live validation

Resolution status:

- not fixed yet
- sync Jetson system time before trusting web report timestamps or build times

### Practical Takeaway After the 2026-03-20 Pass

- For host-side visualization, make sure the CARLA window is on the HDMI output that the Pi really captures.
- For Jetson-side color correctness, keep the C++ detector `swap_rb` control available.
- For 1080p30 RTP receive stability, prioritize the `udpsrc buffer-size + rtpjitterbuffer` receive path over further detector-side tuning.
- If a quick proof run is needed while the full detector path is being rechecked, use isolated OpenCV capture tests first to separate transport failures from inference failures.

## Troubleshooting

- If `gst-launch-1.0` is missing, install the Pi-side GStreamer packages first.
- If Pi capture fails with memory or size errors, re-check `/dev/video0` with `v4l2-ctl --get-fmt-video` and force `RGB3 1920x1080` again.
- If Jetson receives no frames, check `ss -lunp | grep ':5000'` on Jetson. A stale `rtp_cam_node` on port `5000` was a real blocker during live testing.
- If Jetson loses internet after adding the direct cable, remove the `eth0` default gateway and keep Wi-Fi as the default route.
- `NEEDS_CONFIRMATION`: the checked Jetson wrote a `2025-03-28T17:15:21Z` timestamp into the metrics JSON during a March 2026 validation run. Sync Jetson system time before using report timestamps as source-of-truth.
- The C++ detector log may still emit GStreamer `gst_buffer_resize_range` warnings while continuing to process frames. Treat them as a warning to investigate, not as proof that the path is dead.

## Headed CARLA Front RGB Bring-Up on 2026-03-20

New local helper scripts were added for the headed single-camera workflow:

- `hil_runtime/host/scripts/start_carla_headed.sh`
- `hil_runtime/host/scripts/carla_front_rgb_preview.py`
- `hil_runtime/host/scripts/start_carla_front_rgb_preview.sh`

Purpose of the new helpers:

- start a headed CARLA container on the host X11 display instead of `-RenderOffScreen`
- attach a single front RGB camera using `configs/sensors/front_rgb.yaml`
- show the camera feed in a fullscreen preview window that the Pi can capture through HDMI
- keep the existing Pi RTP sender and Jetson C++ detector unchanged

Important remote-runtime note:

- the remote repo mount `/home/du/ros2-humble/src/carla_web_platform` was owned by `501:staff` during validation, so the new scripts could not be copied there directly with `scp`
- for live validation they were staged under `/home/du/duckpark_tmp/` on the host and `/tmp/` inside `ros2-dev`
- local source remains the source of truth for these helpers

Observed issues while bringing up headed CARLA:

1. The first preview runs still showed a front yard / house view and `detection_count=0`.
2. Preview logs reported `spawned ego vehicle ... location=(0.00,0.00,0.00)` even though `Town01` exposed `255` spawn points through the CARLA API.
3. This suggested `load_world("Town01")` finished returning before actor spawning was actually reliable, so the camera path kept falling back to the default transform.

What changed in the preview helper:

- force daytime weather with `ClearNoon` by default
- prefer map spawn points before the fallback transform
- wait for map spawn points to become available
- retry road spawn points before falling back
- if fallback still happens, immediately relocate the ego vehicle onto the first valid map spawn point

Final headed validation state:

- host headed CARLA container was running on `DISPLAY=:1`
- Pi kept sending `1920x1080@30` RTP to Jetson
- Jetson C++ detector stayed on the existing `udp://0.0.0.0:5000` path with `swap_rb=1`
- latest Jetson metrics during the headed CARLA run:
  - `processed_frames=8404`
  - `detection_count=2059`
  - `last_detection_count` was observed reaching `2` during live polling
  - `avg_latency_ms=54.900`
  - `output_fps=8.730`

Visual validation snapshots captured during this run:

- a road-view Jetson screenshot without a hit: `/tmp/duckpark_jetson_preview_v3.png`
- a later Jetson screenshot captured when `last_detection_count=2`: `/tmp/duckpark_jetson_preview_hit.png`

Current practical conclusion:

- the full chain `headed CARLA -> host front RGB preview -> Pi HDMI capture -> RTP -> Jetson C++ detector display` was brought up successfully
- the Jetson screen showed the live CARLA front-view video while inference continued running
- visible detection boxes are scene-dependent frame to frame, but positive detections were confirmed again during the headed CARLA pass

## Town10HD_Opt Display-Mode A/B on 2026-03-20

Goal of this comparison:

- compare the existing path
  - `CARLA sensor -> Python raw_data -> OpenCV fullscreen window -> HDMI -> Pi`
- against a lighter path
  - `CARLA native render window with spectator follow -> HDMI -> Pi`

Both modes were exercised on the live host `192.168.110.151` with:

- headed CARLA on `DISPLAY=:1`
- map `Town10HD_Opt`
- `ClearNoon`
- `20` background traffic vehicles
- the same `front_rgb` camera pose as the reference forward view

Implementation note:

- instead of creating a second script for the comparison, `hil_runtime/host/scripts/carla_front_rgb_preview.py` was extended with:
  - `--display-mode sensor_preview`
  - `--display-mode native_follow`
- `native_follow` does not create an RGB sensor or an OpenCV window
- it only keeps the CARLA spectator aligned with the forward camera pose relative to `hero`

Observed live results:

### A. `sensor_preview` on Town10HD_Opt

- preview log stabilized mostly between `55` and `64 fps`
- sample worker line:
  - `preview fps=63.90 frames=1260`
- sample process usage inside `ros2-dev`:
  - preview Python process around `143%` CPU
- sample container stats:
  - `carla-headed   54.27% CPU`
  - `ros2-dev       30.17% CPU`

### B. `native_follow` on Town10HD_Opt

- follow loop stabilized around `59.3 Hz`
- sample worker line:
  - `native_follow loop_hz=59.30 updates=2340`
- sample process usage inside `ros2-dev` after the old preview process was cleared:
  - native-follow Python process around `4.6%` CPU
- sample container stats:
  - `carla-headed   157.42% CPU`
  - `ros2-dev       3.21% CPU`

Interpretation:

- both display modes had enough host-side headroom for a `30 fps` HDMI demo on `Town10HD_Opt`
- `sensor_preview` spends substantial CPU in the Python/OpenCV sidecar
- `native_follow` removes that user-space copy/display cost almost completely
- the rendering burden shifts back to the actual CARLA window, which is expected because the Unreal viewport becomes the only displayed image source
- this is a display-path simplification and host-overhead redistribution, not a guaranteed increase in CARLA simulation tick rate

Important compatibility conclusion for later Web-driven runs:

- the current free-drive template and descriptor default still use `fixed_delta_seconds=0.05`, i.e. roughly `20 Hz`
- in the current ScenarioRunner path, frame rate is derived from that sync value
- therefore, even if the native render window is smooth and the HDMI path can carry `30 fps`, Web-started runs will not deliver `30 Hz` of *new scene state* until the run descriptor is changed to around `1/30`

Live integration gap during this A/B pass:

- a quick Pi-side native-follow smoke restart hit:
  - `v4l2src0: Failed to allocate required memory`
- this blocked a clean second end-to-end `Pi -> Jetson` proof for the native-follow variant in the same pass
- because the failure happened at Pi capture startup, it should be treated as a Pi capture/runtime issue rather than proof of a CARLA display-mode incompatibility

Follow-up note on visual quality:

- the headed CARLA helper used during the Town10HD_Opt A/B was still starting CARLA with `-quality-level=Low`
- this was later reconfirmed live on `192.168.110.151` by inspecting the running `carla-headed` container command
- conclusion: the "Town10HD_Opt still looks fake / low-quality" complaint was at least partly caused by the startup quality level, not by `native_follow` itself
- local helper default has since been raised from `Low` to `High` in `hil_runtime/host/scripts/start_carla_headed.sh`
