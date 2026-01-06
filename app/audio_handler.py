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
from utils import validate_path

class AudioPlayer:
    def __init__(self):
        self.eastereggTriggered = False
        self.vlcdevice = settings.vlcdevice
        self.audio_available = True
        self.music_volume = 75  # Initialize music_volume attribute
        self.sfx_volume = 75  # Initialize sfx_volume attribute
        self.music_basefolder = settings.musicBaseFolder
        self.sfx_folder = settings.sfxFolder

        try:
            # Try to initialize VLC with ALSA audio output
            vlc_args = []
            if self.vlcdevice:
                vlc_args.append(self.vlcdevice)
            
            self.vlcinstance = vlc.Instance(vlc_args)
            self.musiclistplayer = self.vlcinstance.media_list_player_new()
            self.sfxplayer = self.vlcinstance.media_player_new()
            self.musicplayer = self.vlcinstance.media_player_new()
            
            logger.info("Audio system initialized successfully")
        except Exception as e:
            logger.warning(f"Audio initialization failed: {e}")
            logger.warning("Running in audio-disabled mode")
            self.audio_available = False
            # Initialize dummy objects to prevent crashes
            self.vlcinstance = None
            self.musiclistplayer = None
            self.sfxplayer = None
            self.musicplayer = None

        atexit.register(self.vstopaudio)

    def execute_audio_command(self, args, dry_run=False):
        """Execute audio commands with proper validation and error handling.
        
        Args:
            args: List where first element is command, rest are arguments
            dry_run: If True, validate but don't execute
            
        Returns:
            Dict with 'success' (bool) and 'message' (str) keys
        """
        if not args or len(args) == 0:
            return ("Audio commands:\n"
                    "  music_volume <0-100>        : Set music volume level\n"
                    "  sfx_volume <0-100>          : Set SFX volume level\n"
                    "  fadeout <0-30>              : Fade out audio over specified seconds\n"
                    "  play_music <music_folder>   : Play music from specified folder\n"
                    "  play_sfx <sfx_file>         : Play sound effect file\n"
                    "  play_song <song_file>       : Play song file (relative to music base folder)\n")
        
        command = args[0].lower()
        try:
            if command == "music_volume":
                if len(args) < 2:
                    raise ValueError("music_volume requires a volume level (0-100)")
                volume = int(args[1])
                if not (0 <= volume <= 100):
                    raise ValueError(f"Invalid volume: {volume}. Must be 0-100")
                if dry_run:
                    return True
                else:
                    self.set_music_volume(volume)
                    return (f"Music volume set to {volume}")
            
            elif command == "sfx_volume":
                if len(args) < 2:
                    raise ValueError("sfx_volume requires a volume level (0-100)")
                volume = int(args[1])
                if not (0 <= volume <= 100):
                    raise ValueError(f"Invalid volume: {volume}. Must be 0-100")
                if dry_run:
                    return True
                else:
                    self.set_sfx_volume(volume)
                    return (f"SFX volume set to {volume}")
            
            elif command == "fadeout":
                if len(args) < 2:
                    raise ValueError("fadeout requires duration in seconds")
                else:
                    fadeout_secs = int(args[1])
                
                if not (0 <= fadeout_secs <= 30):
                    raise ValueError(f"Invalid fadeout duration: {fadeout_secs}. Must be between 0-30 seconds")

                if not self.audio_available:
                    return {"success": False, "message": "Audio not available", "level": "warning"}

                if dry_run:
                    return True
                else:        
                    self.execute_audio_fadeout_command(fadeout_secs)
                    return f"Audio faded out over {fadeout_secs} seconds"
                
            elif command == "play_music":
                if len(args) < 2:
                    raise ValueError("play_music requires a music folder name")
                music_subfolder = args[1]
                music_fullfolder = self.get_music_path(music_subfolder)
                
                # Validate path
                if not validate_path(music_fullfolder):
                    raise ValueError(f"Music folder not found: {music_fullfolder}")

                if not self.audio_available:
                    return {"success": False, "message": "Audio not available", "level": "warning"}
                
                if dry_run:
                    return True
                else:
                    self.playMusic(music_fullfolder)
                    return f"Playing music from {music_fullfolder}"
            
            elif command == "play_sfx":
                if len(args) < 2:
                    raise ValueError("play_sfx requires a sound effect file name")
                sfx_file = args[1]
                sfx_path = self.get_sfx_filepath(sfx_file)
                
                # Validate path
                if not validate_path(sfx_path):
                    raise ValueError(f"SFX file not found: {sfx_path}")
                
                if not self.audio_available:
                    return {"success": False, "message": "Audio not available", "level": "warning"}
                
                if dry_run:
                    return True
                else:
                    self.play_sfx(sfx_path)
                    return f"Playing SFX: {sfx_file}"
            
            elif command == "play_song":
                if len(args) < 2:
                    raise ValueError("play_song requires a song file path (relative to music base folder)")
                song_file = args[1]
                song_path = self.get_music_path(song_file)

                # Validate path
                if not validate_path(song_path):
                    raise ValueError(f"Song file not found: {song_path}")

                if not self.audio_available:
                    return {"success": False, "message": "Audio not available", "level": "warning"}
                
                if dry_run:
                    return True
                else:
                    # Play as SFX (can be extended to detect music vs sfx based on path)
                    self.play_sfx(song_path)
                    return f"Playing audio: {song_path}"
            else:
                raise ValueError(f"Unknown audio command: {command}")
        except Exception as e:
            error_msg = f"Error executing audio command '{command}': {e}"
            #logger.error(error_msg)
            raise RuntimeError(error_msg)
        

    def set_music_volume(self, volume):
        if 0 <= volume <= 100:
            self.music_volume = volume  # Update to use music_volume
            if self.audio_available and self.musicplayer:
                self.musicplayer.audio_set_volume(volume)
                logger.info("Setting music volume at " + str(volume))
        else:
            raise ValueError(f"Invalid music volume level: {volume}. Must be between 0-100.")

    def get_music_volume(self):
        return self.music_volume

    def get_sfx_volume(self):
        return self.sfx_volume

    def set_sfx_volume(self, volume):
        if 0 <= volume <= 100:
            self.sfx_volume = volume
            if self.audio_available and self.sfxplayer:
                self.sfxplayer.audio_set_volume(volume)
                logger.info("Setting SFX volume at " + str(volume))
        else:
            raise ValueError(f"Invalid SFX volume level: {volume}. Must be between 0-100.")

    def get_music_path(self, music_subfolder):
        music_fullfolder = path.join(path.dirname(path.abspath(__file__)), f"{self.music_basefolder}", music_subfolder)
        return music_fullfolder

    def get_sfx_filepath(self, sfx_file):
        return path.join(path.dirname(path.abspath(__file__)), f"{self.sfx_folder}", sfx_file)

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

    def playMusic(self, music_fullfolder):
        if not self.audio_available:
            logger.debug("Audio not available - skipping music playback")
            return
        music_files = self.get_music_files(music_fullfolder)
        self.vplaymusic(music_files)

    def play_sfx(self, sfx_file):
        if not self.audio_available:
            logger.debug("Audio not available - skipping SFX playback")
            return
        self.vplaysfx(sfx_file)

    def get_music_files(self, music_fullfolder, max_files=20):
        music_files = [os.path.join(music_fullfolder, f) for f in os.listdir(music_fullfolder)]  # get complete file paths
        # Filter to keep only valid audio files
        music_files = [f for f in music_files if self.checkaudioext(f)]
        logger.info(f"Added {str(len(music_files))} music files from folder {music_fullfolder}")
        random.shuffle(music_files)  # shuffle list

        if len(music_files) > max_files:
            music_files = music_files[:max_files-1]  # get only the first max_files songs

        if settings.eastereggEnabled and self.eastereggTriggered:
            logger.info("EasterEgg enabled!!")
            easter_egg_folder = self.get_music_path("easteregg")
            easter_egg_files = [os.path.join(easter_egg_folder, f) for f in os.listdir(easter_egg_folder)]  # get complete file paths
            # Filter easter egg files to only include valid audio files
            easter_egg_files = [f for f in easter_egg_files if self.checkaudioext(f)]
            # Add easter egg files at the beginning of the music files list
            music_files = easter_egg_files + music_files
            self.eastereggTriggered = False

        return music_files

    def vplaymusic(self, music_files):
        if not self.audio_available:
            logger.debug("Audio not available - skipping music playback")
            return

        playlist = self.vlcinstance.media_list_new()
        for song in range(len(music_files)):
            playlist.add_media(self.vlcinstance.media_new(music_files[song]))

        self.musiclistplayer.set_media_list(playlist)

        self.musiclistplayer.set_playback_mode(vlc.PlaybackMode.loop)
        self.musiclistplayer.play()

        self.musicplayer = self.musiclistplayer.get_media_player()
        time.sleep(0.1)
        logger.info("Setting music volume at " + str(self.music_volume))

        logger.info("Playing music (first three songs): " + music_files[0] + " " + music_files[1] + " " + music_files[2])

        self.set_music_volume(self.music_volume)

    def vplaysfx(self, sfx_file):
        if not self.audio_available:
            logger.debug("Audio not available - skipping SFX playback")
            return
            
        media = self.vlcinstance.media_new(sfx_file)

        self.sfxplayer.set_media(media)
        self.set_sfx_volume(self.sfx_volume)

        self.sfxplayer.play()
        logger.info(f"Playing sfx : {sfx_file}")

    def vstopaudio(self, fadeout_secs=3):
        try:
            if self.audio_available and (self.music_volume > 0 or self.sfx_volume > 0):
                if self.music_volume > self.sfx_volume:  # calculate pause interval. Takes higher volume
                    fadeoutpause = int(fadeout_secs) / (self.music_volume * 1.0)
                else:
                    fadeoutpause = int(fadeout_secs) / (self.sfx_volume * 1.0)

                logger.info("Fading out in " + str(fadeout_secs) + " seconds")

                mvol = self.music_volume
                svol = self.sfx_volume

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

    def execute_audio_fadeout_command(self, fadeout_secs):
        music_volume = self.musicplayer.audio_get_volume()
        sfx_volume = self.sfxplayer.audio_get_volume()
        self.vstopaudio(fadeout_secs)
        self.set_music_volume(music_volume)
        self.set_sfx_volume(sfx_volume)

    # def execute_playmusic_command(self, music_folder):
    #     gpio = self.mygpio_handler.GPIOMap[settings.startButtonGPIOName]
    #     if self.GPIO.input(gpio) == 1:
    #         self.setEasterEggTrigger(True)
    #     self.playMusic(music_folder)

    def setEasterEggTrigger(self, easter_egg_trigger):
        self.eastereggTriggered = easter_egg_trigger
