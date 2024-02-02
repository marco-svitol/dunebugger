from dunebuggerlogging import logger
import os, random, vlc, time, app.supervisor.InTime as InTime
from datetime import datetime
from dunebugger_settings import settings

normalMusicVolume = 95
normalSfxVolume = 90
musicVolume = normalMusicVolume
sfxVolume = normalSfxVolume
quietMusicVol = 95
quietSfxVol = 90
ignoreQuietTime = True
fadeoutsec = 8 #fade out seconds
musicpath = "../music/"
sfxpath = "../sfx/"
sfxfile = "2009.mp3"
easteregg = "ohhche.mp3"
entrysong = "fincosong2022.mp3"
sfxuccelli = "allodole.mp3"

def vplaymusic(customsong):
    playlist = vlcinstance.media_list_new()

    fileplaylist = os.listdir(musicpath) #get filenames
    logger.info("Music: read " + str(len(fileplaylist)) + " files from folder " + musicpath)

    for mfile in fileplaylist: #keep only if extension is valid audio file
        if not checkaudioext(mfile):
            fileplaylist.remove(mfile)

    random.shuffle(fileplaylist)  # shuffle list
	
    if len(fileplaylist) > 20:
        fileplaylist = fileplaylist[:19]  # get only first 20 songs  

    if customsong: #eastereggg
        logger.info("EasterEgg enabled!!")
        playlist.add_media(vlcinstance.media_new(sfxpath + easteregg))
        playlist.add_media(vlcinstance.media_new(sfxpath + "A.mp3"))

    for song in range(len(fileplaylist)):  # add path to songname
        playlist.add_media(vlcinstance.media_new(musicpath + fileplaylist[song]))

    musiclistplayer.set_media_list(playlist)

    musiclistplayer.set_playback_mode(vlc.PlaybackMode.loop)
    musiclistplayer.play()

    musicplayer = musiclistplayer.get_media_player()
    time.sleep(0.1)
    logger.info("Setting music volume at "+str(musicVolume))
    musicplayer.audio_set_volume(musicVolume)

    logger.info("Playing music (first three songs): " + fileplaylist[0] + " " + fileplaylist[1] + " " + fileplaylist[2])

def vplaysfx(filename):
    media = vlcinstance.media_new(sfxpath + filename)

    sfxplayer.set_media(media)
    logger.info("Setting sfx volume at "+str(sfxVolume))
    sfxplayer.audio_set_volume(sfxVolume)

    sfxplayer.play()
    logger.info("Playing sfx :" + sfxpath + filename)

def checkaudioext(filename):
    audioext = ['AAC', 'AC3', 'AIFF', 'AMR', 'AU', 'FLAC', 'M4A', 'MIDI', 'MKA', 'MP3', 'OGA', 'RA', 'VOC', 'WAV', 'WMA']
    if filename[-3:].upper() in audioext:
        return True
    return False

def vstopaudio():
    try:
        if musicVolume >0 or sfxVolume > 0:
            if musicVolume > sfxVolume: # calculate pause interval. Takes higher volume
                fadeoutpause = fadeoutsec / (musicVolume * 1.0)
            else:
                fadeoutpause = fadeoutsec / (sfxVolume * 1.0)

            logger.info("Fading out in " + str(fadeoutsec) + " seconds")

            mvol = musicVolume
            svol = sfxVolume

            while (mvol>0 or svol > 0):
                if musicplayer is not None and mvol > 0: mvol-=1; musicplayer.audio_set_volume(mvol)
                if sfxplayer is not None and svol > 0: svol-=1; sfxplayer.audio_set_volume(svol)
                print ('.',end="",flush=True)
                time.sleep(fadeoutpause)
            logger.info('Stopping music and sfx player')
            musiclistplayer.stop()
            sfxplayer.stop()
    except:
        logger.warning("vstopaudio exception, most probably sound was not even playing.")
        return

def initMusic():
    #check current date against calendar delle messe per impostare volume            
    musicVolume = normalMusicVolume
    sfxVolume = normalSfxVolume
    logger.debug("MusicVolume: "+str(musicVolume)+" SfxVolume: "+str(sfxVolume))
    if not ignoreQuietTime:
        if not isinstance(InTime.getNTPTime(),int): #time not synced
            musicVolume = quietMusicVol
            sfxVolume = quietSfxVol
            logger.info("Orario non sincronizzato: vol musica="+str(musicVolume)+" vol sfx="+str(sfxVolume))
        elif InTime.duranteCelebrazioni(datetime.now(),settings.cyclelength):
            musicVolume = quietMusicVol
            sfxVolume = quietSfxVol
            logger.info("Siamo durante una celebrazione: vol music="+str(musicVolume)+" vol sfx="+str(sfxVolume))

    # Lista di (Time,Action) - ordina la lista - eseguo una runpending() che scansiona la lista ed esegue action
    musicplayer.audio_set_channel(1)

vlcinstance = vlc.Instance('--aout=alsa')
musiclistplayer = vlcinstance.media_list_player_new()
sfxplayer = vlcinstance.media_player_new()
musicplayer = vlcinstance.media_player_new()