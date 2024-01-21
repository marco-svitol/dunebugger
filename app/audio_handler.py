from dunebuggerlogging import logger
import os
import random
import vlc
import time
import supervisor.InTime as InTime
from datetime import datetime

class AudioPlayer:
    def __init__(self):
        self.normalMusicVolume = 95
        self.normalSfxVolume = 90
        self.musicVolume = self.normalMusicVolume
        self.sfxVolume = self.normalSfxVolume
        self.quietMusicVol = 95
        self.quietSfxVol = 90
        self.ignoreQuietTime = True
        self.fadeoutsec = 8  # fade out seconds
        self.musicpath = "../music/"
        self.sfxpath = "../sfx/"
        self.sfxfile = "2009.mp3"
        self.easteregg = "ohhche.mp3"
        self.entrysong = "fincosong2022.mp3"
        self.sfxuccelli = "allodole.mp3"

        self.vlcinstance = vlc.Instance('--aout=alsa')
        self.musiclistplayer = self.vlcinstance.media_list_player_new()
        self.sfxplayer = self.vlcinstance.media_player_new()
        self.musicplayer = self.vlcinstance.media_player_new()

        #self.initMusic()

    def checkaudioext(self, filename):
        audioext = ['AAC', 'AC3', 'AIFF', 'AMR', 'AU', 'FLAC', 'M4A', 'MIDI', 'MKA', 'MP3', 'OGA', 'RA', 'VOC', 'WAV', 'WMA']
        if filename[-3:].upper() in audioext:
            return True
        return False

    def vplaymusic(self, customsong):
        playlist = self.vlcinstance.media_list_new()

        fileplaylist = os.listdir(self.musicpath)  # get filenames
        logger.info("Music: read " + str(len(fileplaylist)) + " files from folder " + self.musicpath)

        for mfile in fileplaylist:  # keep only if extension is a valid audio file
            if not self.checkaudioext(mfile):
                fileplaylist.remove(mfile)

        random.shuffle(fileplaylist)  # shuffle list

        if len(fileplaylist) > 20:
            fileplaylist = fileplaylist[:19]  # get only the first 20 songs

        if customsong:  # easteregg
            logger.info("EasterEgg enabled!!")
            playlist.add_media(self.vlcinstance.media_new(self.sfxpath + self.easteregg))
            playlist.add_media(self.vlcinstance.media_new(self.sfxpath + "A.mp3"))

        for song in range(len(fileplaylist)):  # add path to songname
            playlist.add_media(self.vlcinstance.media_new(self.musicpath + fileplaylist[song]))

        self.musiclistplayer.set_media_list(playlist)

        self.musiclistplayer.set_playback_mode(vlc.PlaybackMode.loop)
        self.musiclistplayer.play()

        self.musicplayer = self.musiclistplayer.get_media_player()
        time.sleep(0.1)
        logger.info("Setting music volume at " + str(self.musicVolume))
        self.musicplayer.audio_set_volume(self.musicVolume)

        logger.info("Playing music (first three songs): " + fileplaylist[0] + " " + fileplaylist[1] + " " +
                    fileplaylist[2])

    def vplaysfx(self, filename):
        media = self.vlcinstance.media_new(self.sfxpath + filename)

        self.sfxplayer.set_media(media)
        logger.info("Setting sfx volume at " + str(self.sfxVolume))
        self.sfxplayer.audio_set_volume(self.sfxVolume)

        self.sfxplayer.play()
        logger.info("Playing sfx :" + self.sfxpath + filename)

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
                logger.info('Stopping music and sfx player')
                self.musiclistplayer.stop()
                self.sfxplayer.stop()
        except:
            logger.warning("vstopaudio exception, most probably sound was not even playing.")
            return

    def musicSetVolume(self, vol):
        self.musicplayer.audio_set_volume(vol)
    
    def sfxSetVolume(self, vol):
        self.sfxplayer.audio_set_volume(vol)

    def initMusic(self):
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

