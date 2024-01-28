from dunebuggerlogging import logger
import os
import random
import vlc
import time
import supervisor.InTime as InTime
from datetime import datetime
from dunebugger_settings import settings
from os import path

class AudioPlayer:
    def __init__(self):
        self.normalMusicVolume = settings.normalMusicVolume
        self.normalSfxVolume = settings.normalSfxVolume
        self.musicVolume = self.normalMusicVolume
        self.sfxVolume = self.normalSfxVolume
        self.quietMusicVol = settings.quietMusicVol
        self.quietSfxVol = settings.quietSfxVol
        self.ignoreQuietTime = settings.ignoreQuietTime
        self.fadeoutsec = settings.fadeoutsec
        self.musicpath = path.join(path.dirname(path.abspath(__file__)), settings.musicpath)
        self.sfxpath = path.join(path.dirname(path.abspath(__file__)), settings.sfxpath)
        self.sfxfile = settings.sfxfile
        self.easteregg = settings.easteregg
        self.entrysong = settings.entrysong
        self.vlcdevice = settings.vlcdevice

        self.vlcinstance = vlc.Instance(self.vlcdevice)
        self.musiclistplayer = self.vlcinstance.media_list_player_new()
        self.sfxplayer = self.vlcinstance.media_player_new()
        self.musicplayer = self.vlcinstance.media_player_new()

        #self.initMusic()

    def checkaudioext(self, filename):
        audioext = ['AAC', 'AC3', 'AIFF', 'AMR', 'AU', 'FLAC', 'M4A', 'MIDI', 'MKA', 'MP3', 'OGA', 'RA', 'VOC', 'WAV', 'WMA']
        if filename[-3:].upper() in audioext:
            return True
        return False

    def startAudio(self, easterEggOn = False):
        audioPlayer.vplaymusic(easterEggOn)
        audioPlayer.vplaysfx()

    def vplaymusic(self, easterEggOn):

        self.setVolumeBasedOntime()

        playlist = self.vlcinstance.media_list_new()

        fileplaylist = os.listdir(self.musicpath)  # get filenames
        logger.info("Music: read " + str(len(fileplaylist)) + " files from folder " + self.musicpath)

        for mfile in fileplaylist:  # keep only if extension is a valid audio file
            if not self.checkaudioext(mfile):
                fileplaylist.remove(mfile)

        random.shuffle(fileplaylist)  # shuffle list

        if len(fileplaylist) > 20:
            fileplaylist = fileplaylist[:19]  # get only the first 20 songs

        if easterEggOn:  # easteregg
            logger.info("EasterEgg enabled!!")
            playlist.add_media(self.vlcinstance.media_new(self.sfxpath + self.easteregg))

        for song in range(len(fileplaylist)):  # add path to songname
            playlist.add_media(self.vlcinstance.media_new(self.musicpath + fileplaylist[song]))

        self.musiclistplayer.set_media_list(playlist)

        self.musiclistplayer.set_playback_mode(vlc.PlaybackMode.loop)
        self.musiclistplayer.play()

        self.musicplayer = self.musiclistplayer.get_media_player()
        time.sleep(0.1)
        logger.info("Setting music volume at " + str(self.musicVolume))

        logger.info("Playing music (first three songs): " + fileplaylist[0] + " " + fileplaylist[1] + " " +
                    fileplaylist[2])
        
        self.musicSetVolume(self.musicVolume)
        

    def vplaysfx(self):
        sfxfile = path.join(self.sfxpath, self.sfxfile)
        media = self.vlcinstance.media_new(sfxfile)

        self.sfxplayer.set_media(media)
        self.sfxSetVolume(self.sfxVolume)

        self.sfxplayer.play()
        logger.info(f"Playing sfx : {sfxfile}")

    def vstopaudio(self):
        try:
            if self.musicVolume > 0 or self.sfxVolume > 0:
                if self.musicVolume > self.sfxVolume:  # calculate pause interval. Takes higher volume
                    fadeoutpause = self.fadeoutsec / (self.musicVolume * 1.0)
                else:
                    fadeoutpause = self.fadeoutsec / (self.sfxVolume * 1.0)

                logger.info("Fading out in " + str(self.fadeoutsec) + " seconds")

                mvol = self.musicVolume
                svol = self.sfxVolume

                while mvol > 0 or svol > 0:
                    if self.musicplayer is not None and mvol > 0:
                        mvol -= 1
                        self.musicplayer.audio_set_volume(mvol)
                    if self.sfxplayer is not None and svol > 0:
                        svol -= 1
                        self.sfxplayer.audio_set_volume(svol)
                    print('.', end="", flush=True)
                    time.sleep(fadeoutpause)
                print(f'\n')
                self.musiclistplayer.stop()
                self.sfxplayer.stop()
        except:
            logger.warning("vstopaudio exception, most probably sound was not even playing.")
            return

    def musicSetVolume(self, vol):
        self.musicplayer.audio_set_volume(vol)
        logger.info("Setting music volume at " + str(vol))
    
    def sfxSetVolume(self, vol):
        self.sfxplayer.audio_set_volume(vol)
        logger.debug("Setting sfx volume at " + str(vol))

    def setVolumeBasedOntime(self):
        # check current date against calendar delle messe per impostare volume
        self.musicVolume = self.normalMusicVolume
        self.sfxVolume = self.normalSfxVolume
        logger.debug("MusicVolume: " + str(self.musicVolume) + " SfxVolume: " + str(self.sfxVolume))
        if not self.ignoreQuietTime:
            if not isinstance(InTime.getNTPTime(), int):  # time not synced
                self.musicVolume = self.quietMusicVol
                self.sfxVolume = self.quietSfxVol
                logger.info("Orario non sincronizzato: vol musica=" + str(self.musicVolume) + " vol sfx=" + str(self.sfxVolume))
            elif InTime.duranteCelebrazioni(datetime.now(), 372):
                self.musicVolume = self.quietMusicVol
                self.sfxVolume = self.quietSfxVol
                logger.info("Siamo durante una celebrazione: vol music=" + str(self.musicVolume) + " vol sfx=" + str(self.sfxVolume))

audioPlayer = AudioPlayer()

