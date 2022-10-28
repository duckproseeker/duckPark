#include "Mplayer.h"
#include <iostream>

bool WavPlayer::_pcm_open()
{
    int rc = snd_pcm_open(&handle, "default", SND_PCM_STREAM_PLAYBACK, 0);
    
    return rc < 0 ? false : true;
}

bool WavPlayer::_pcm_init()
{
    snd_pcm_hw_params_alloca(&params);
    int rc = snd_pcm_hw_params_any(handle, params);
    if(rc < 0)
    {
        return false;
    }
    //初始化访问权限
    int rc = snd_pcm_hw_params_set_access(handle, params, SND_PCM_ACCESS_RW_INTERLEAVED);
    if(rc < 0)
    {
        std::cerr << "设置访问权限失败" << std::endl;
        return false;
    }
}

int WavPlayer::_set_pcm_play(FILE* fp)
{
    int ret;
    int size;
    unsigned int val;
    int dir = 0;
    char *buffer;
    int channels = wav_header.wChannels;
    int frequency = wav_header.nSamplesPersec;
    int bit = wav_header.wBitsPerSample;
    int datablock = wav_header.wBlockAlign;
    unsigned char ch[100];   //用来存储wav文件的头信息

    if(_pcm_open() == false)
    {
        std::cerr << "open PCM device failed !" << std::endl;
        return 1; 
    }

    if(_pcm_init() == false)
    {
        std::cerr << "Init PCM device failed !" << std::endl;
        return 1;
    }

    //采样位数
    switch(bit/8)
    {
        case 1:
            snd_pcm_hw_params_set_format(handle, params, SND_PCM_FORMAT_U8);
            break;
        case 2:
            snd_pcm_hw_params_set_format(handle, params, SND_PCM_FORMAT_S16_LE);
            break;
        case 3:
            snd_pcm_hw_params_set_format(handle, params, SND_PCM_FORMAT_S24_LE);
            break;
    }

    //设置声道 1：单声道，2：立体声

    

}

void WavPlayer::onplay(const char* file)
{
    int nread;
    FILE* fp = fopen(file, "rb");
    if(fp == NULL)
    {
        std::cerr << "open file failed !" << std::endl;
        return;
    }

    nread = fread(&wav_header, 1, sizeof(wav_header), fp);
        printf("nread=%d\n",nread);
    
    printf("文件大小rLen: %d\n",wav_header.rLen);   
    printf("声道数：%d\n",wav_header.wChannels);
    printf("采样频率：%d\n",wav_header.nSamplesPersec);
    printf("采样的位数：%d\n",wav_header.wBitsPerSample);   
    printf("wSampleLength=%d\n",wav_header.wSampleLength);

    _set_pcm_play(fp);
}
