#include <alsa/asoundlib.h>
#include <stdlib.h>

#pragma pack(1)
struct WAV_HEADER
{
    char rld[4];            //riff标志符号
    int rLen;
    char wld[4];            //格式符号（wave）
    char fld[4];            //"fmt"

    int fLen;               //sizeof(wave format matex)

    short wFormatTag;       //编码格式
    short wChannels;        //声道数
    int nSamplesPersec;     //采样频率
    int nAvgBitsPerSample;  //WAVE文件采样大小
    short wBlockAlign;      //块对齐
    short wBitsPerSample;   //WAVE文件采样大小

    char dld[4];            //"data"
    int wSampleLength;      //音频数据的大小

};


class WavPlayer
{
public:

    void onplay(const char*);

private:
    int _set_pcm_play(FILE *fp);

    bool _pcm_open();             //打开PCM设备

    bool _pcm_init();             //初始化设备


private:

    snd_pcm_t* handle;            //PCI设备句柄
    
    snd_pcm_hw_params_t* params;  //硬件信息和PCM配置

    snd_pcm_uframes_t frames;

    WAV_HEADER wav_header;        //音频文件的头部

};