import os
import random
import vlc
import time
# import supervisor.InTime as InTime
# from datetime import datetime
from os import path
import atexit

from dunebugger_settings import settings
from dunebugger_logging import logger


class AudioPlayer:
    def __init__(self):
        self.musicVolume = settings.normalMusicVolume
        self.sfxVolume = settings.normalSfxVolume
        self.eastereggTriggered = False
        self.vlcdevice = settings.vlcdevice

        self.vlcinstance = vlc.Instance(self.vlcdevice)
        self.musiclistplayer = self.vlcinstance.media_list_player_new()
        self.sfxplayer = self.vlcinstance.media_player_new()
        self.musicplayer = self.vlcinstance.media_player_new()

        atexit.register(self.vstopaudio)

    def set_music_volume(self, volume):
        if 0 <= volume <= 100:
            self.musicVolume = volume
            self.musicSetVolume(volume)
        else:
            logger.warning(f"Invalid music volume level: {volume}. Must be between 0-100.")
    
    def get_music_volume(self):
        return self.musicVolume
    
    def get_sfx_volume(self):
        return self.sfxVolume

    def set_sfx_volume(self, volume):
        if 0 <= volume <= 100:
            self.sfxVolume = volume
            self.sfxSetVolume(volume)
        else:
            logger.warning(f"Invalid SFX volume level: {volume}. Must be between 0-100.")

    def get_music_path(self, music_folder):
        return path.join(path.dirname(path.abspath(__file__)), "..", music_folder)

    def get_sfx_filepath(self, sfx_file):
        return path.join(path.dirname(path.abspath(__file__)), "..", sfx_file)

    def checkaudioext(self, filename):
        audioext = [
            "AAC",
            "AC3",
            "AIFF",
            "AMR",
            "AU",
            "FLAC",
            "M4A",
            "MIDI",
            "MKA",
            "MP3",
            "OGA",
            "RA",
            "VOC",
            "WAV",
            "WMA",
        ]
        if filename[-3:].upper() in audioext:
            return True
        return False

    def playMusic(self, music_folder):
        self.vplaymusic(music_folder)

    def play_sfx(self, sfx_file):
        self.vplaysfx(sfx_file)

    def vplaymusic(self, music_folder):

        self.setVolumeBasedOntime()

        playlist = self.vlcinstance.media_list_new()

        fileplaylist = os.listdir(music_folder)  # get filenames
        logger.info(f"Music: read {str(len(fileplaylist))} files from folder {music_folder}")

        for mfile in fileplaylist:  # keep only if extension is a valid audio file
            if not self.checkaudioext(mfile):
                fileplaylist.remove(mfile)

        random.shuffle(fileplaylist)  # shuffle list

        if len(fileplaylist) > 20:
            fileplaylist = fileplaylist[:19]  # get only the first 20 songs

        if settings.eastereggEnabled and self.eastereggTriggered:
            logger.info("EasterEgg enabled!!")
            playlist.add_media(self.vlcinstance.media_new(self.get_sfx_filepath("app_audio_files/ohhche.mp3")))
            playlist.add_media(self.vlcinstance.media_new(self.get_music_path("app_audio_files/dunebuggy.mp3")))
            self.eastereggTriggered = False

        for song in range(len(fileplaylist)):  # add path to songname
            playlist.add_media(self.vlcinstance.media_new(music_folder + "/" + fileplaylist[song]))

        self.musiclistplayer.set_media_list(playlist)

        self.musiclistplayer.set_playback_mode(vlc.PlaybackMode.loop)
        self.musiclistplayer.play()

        self.musicplayer = self.musiclistplayer.get_media_player()
        time.sleep(0.1)
        logger.info("Setting music volume at " + str(self.musicVolume))

        logger.info("Playing music (first three songs): " + fileplaylist[0] + " " + fileplaylist[1] + " " + fileplaylist[2])

        self.musicSetVolume(self.musicVolume)

    def vplaysfx(self, sfx_file):
        media = self.vlcinstance.media_new(sfx_file)

        self.sfxplayer.set_media(media)
        self.sfxSetVolume(self.sfxVolume)

        self.sfxplayer.play()
        logger.info(f"Playing sfx : {sfx_file}")

    def vstopaudio(self, fadeout_secs=3):
        try:
            if self.musicVolume > 0 or self.sfxVolume > 0:
                if self.musicVolume > self.sfxVolume:  # calculate pause interval. Takes higher volume
                    fadeoutpause = int(fadeout_secs) / (self.musicVolume * 1.0)
                else:
                    fadeoutpause = int(fadeout_secs) / (self.sfxVolume * 1.0)

                logger.info("Fading out in " + str(fadeout_secs) + " seconds")

                mvol = self.musicVolume
                svol = self.sfxVolume

                while mvol > 0 or svol > 0:
                    if self.musicplayer is not None and mvol > 0:
                        mvol -= 1
                        self.musicplayer.audio_set_volume(mvol)
                    if self.sfxplayer is not None and svol > 0:
                        svol -= 1
                        self.sfxplayer.audio_set_volume(svol)
                    print(".", end="", flush=True)
                    time.sleep(fadeoutpause)
                print("\n")
                self.musiclistplayer.stop()
                self.sfxplayer.stop()
        except Exception as e:
            logger.warning(f"vstopaudio exception: {e}")
            return

    def musicSetVolume(self, vol):
        self.musicplayer.audio_set_volume(vol)
        logger.info("Setting music volume at " + str(vol))

    def sfxSetVolume(self, vol):
        self.sfxplayer.audio_set_volume(vol)
        logger.debug("Setting sfx volume at " + str(vol))

    # def setVolumeBasedOntime(self):
    #     # check current date against calendar delle messe per impostare volume
    #     self.musicVolume = self.normalMusicVolume
    #     self.sfxVolume = self.normalSfxVolume
    #     logger.debug("MusicVolume: " + str(self.musicVolume) + " SfxVolume: " + str(self.sfxVolume))
    #     if not self.ignoreQuietTime:
    #         if not isinstance(InTime.getNTPTime(), int):  # time not synced
    #             self.musicVolume = self.quietMusicVol
    #             self.sfxVolume = self.quietSfxVol
    #             logger.info("Orario non sincronizzato: vol musica=" + str(self.musicVolume) + " vol sfx=" + str(self.sfxVolume))
    #         elif InTime.duranteCelebrazioni(datetime.now(), 372):
    #             self.musicVolume = self.quietMusicVol
    #             self.sfxVolume = self.quietSfxVol
    #             logger.info("Siamo durante una celebrazione: vol music=" + str(self.musicVolume) + " vol sfx=" + str(self.sfxVolume))

    def setEasterEggTrigger(self, easter_egg_trigger):
        self.eastereggTriggered = easter_egg_trigger
