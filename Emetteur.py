import pyaudio
import matplotlib.pyplot as plt
import numpy as np
import simpleaudio as sa

def crc(msg, div, code='000'): #Cette fonction peut generer un CRC sur 3 bits et le verifier
    msg = msg + code
    msg = list(msg)
    div = list(div)
    for i in range(len(msg)-len(code)):
        if msg[i] == '1':
            for j in range(len(div)):
                msg[i+j] = str((int(msg[i+j])+int(div[j]))%2)
    return ''.join(msg[-len(code):])

def str_vers_bin(txt): #Converti une chaine de caractère en binaire.
    def dec_vers_bin(x): #Converti un nombre decimal en binaire
        return int(bin(x)[2:]) #Converti x, un nombre decimal en binaire
    txt_Binaire = []
    for i in list(txt): #Prend chaque lettre de txt et la stock dans i
        Lettre = list(str(dec_vers_bin(ord(i)))) #Converti une lettre en nombre binaire (stocker dans une list str)
        Lettre = [int(i) for i in Lettre] #Converti la list str en list int
        if len(Lettre) < 7: #Met sur 7 bits
            for i in range(0,7-len(Lettre)) :
                Lettre.insert(0, 0)
        txt_Binaire.extend(Lettre) #Ajoute chaque lettre dans une List
    return(txt_Binaire)

def bin_vers_txt(binary): #Converti un caractère binaire vers texte.  
    binary1 = binary 
    decimal, i, n = 0, 0, 0
    while(binary != 0): 
        dec = binary % 10
        decimal = decimal + dec * pow(2, i) 
        binary = binary//10
        i += 1
    return(chr(decimal))

def Emission_Message(txt,frbit1,frbit0,fs,Baud_Rate,favionStart,favionFin): # Cette fonction emmet un message texte en audio
    DonnéesBinaire = str_vers_bin(txt)
    Temps_par_bits = 1/Baud_Rate
    Données = []
    Données_str = [str(int) for int in DonnéesBinaire]
    str_of_ints = "".join(Données_str)
    list_of_str = list(crc(str_of_ints, '1011'))
    for i in range(0, len(list_of_str)): 
        list_of_str[i] = int(list_of_str[i])
    Données.extend(favionStart) 
    Données.extend(DonnéesBinaire) 
    Données.extend(list_of_str)
    Données.extend(favionFin) 
    seconds = len(Données)*Temps_par_bits
    Données_multi = np.repeat(Données, seconds*fs/len(Données))
    t = np.linspace(0, seconds, int(seconds * fs), False)
    note = np.sin(frbit1 * t * 2 * np.pi)*Données_multi + np.sin(frbit0 * t * 2 * np.pi)*abs(Données_multi-1)
    audio = note * (2**15 - 1) / np.max(np.abs(note)) #Ensure that highest value is in 16-bit range
    audio = audio.astype(np.int16) #Convert to 16-bit data 
    play_obj = sa.play_buffer(audio, 1, 2, fs) #Start playback
    play_obj.wait_done()

def Ecoute_données(FavionStart,FavionFin,fs,Seuil_activation,frbit1,frbit0):#Cette fonction écoute et renvoi les données entre les deux fanions
    print("Recherche de données...")
    CHUNK = 441
    FORMAT = pyaudio.paInt16
    audio = pyaudio.PyAudio()
    echelle = CHUNK/fs #Pour prendre la bonne valeur dans fft
    stream = audio.open(format=FORMAT, channels=1,rate=fs, input=True,frames_per_buffer=CHUNK)
    bitetude = []
    reception_en_cours = False
    for i in range(len(FavionStart)):
        bitetude.append(0)
    pas = 0
    Donné_r = []
    while True:
        data = stream.read(CHUNK)
        data1 = np.frombuffer(data,dtype=np.int16)
        fft_data = (np.abs(np.fft.fft(data1)))
        Aplival = fft_data[int(frbit0*echelle)]
        Aplival2 = fft_data[int(frbit1*echelle)]
        if Aplival2 > Aplival and (Aplival2>Seuil_activation or Aplival>Seuil_activation):
            bitactuel = 1
        else:
            bitactuel = 0        
        if pas == 0:  # Pour prendre que un bit sur 10
            for i in range(0,len(bitetude)-1):
                bitetude[i] = bitetude[i+1]
            bitetude[len(bitetude)-1] = bitactuel  
            if reception_en_cours == True:
                Donné_r.extend([bitactuel])
            if bitetude == FavionStart and reception_en_cours == False:
                reception_en_cours = True
                print("Reception en cours....")
            if bitetude == FavionFin and reception_en_cours == True:
                reception_en_cours = False
                print("Fin de reception")
                return(Donné_r)
            
        if pas == 9: # Pour prendre que un bit sur 10
            pas = 0
        else:
            pas = pas + 1 
            
def Données_vers_text(données,taille_favion): #Convertit un tableau de données en chaine de caractère.
    Message = ""
    for ii in range(0,len(données)-taille_favion-4,7):
        bit = ""
        for i in range(0+ii,7+ii):
            bit = bit + str(données[i])
        Lettre = bin_vers_txt(int(bit))
        Message = Message + Lettre
    crc = []
    for a in range(len(données)-taille_favion-3,len(données)-taille_favion):
        crc.extend([int(données[a])])
    Données_brut = []
    for a in range(0,len(données)-taille_favion-3):
        Données_brut.extend([int(données[a])])
    Données_en_str = [str(int) for int in Données_brut]
    Données_en_str1 = "".join(Données_en_str)
    Code_en_str = [str(int) for int in crc]
    Code_en_str1 = "".join(Code_en_str)
    return [Code_en_str1,Données_en_str1,Message]

def Ecoute_Reponse(code,temps_ecoute,fs,Seuil_activation,frbit1,frbit0): # Cette fonction ecoute la réponse peadant temps_ecoute revoie True si il y a une réponse
    CHUNK = 441
    FORMAT = pyaudio.paInt16
    audio = pyaudio.PyAudio()
    echelle = CHUNK/fs #Pour prendre la bonne valeur dans fft
    stream = audio.open(format=FORMAT, channels=1,rate=fs, input=True,frames_per_buffer=CHUNK)
    bitetude = []
    for i in range(len(code)):
        bitetude.append(0)
    pas = 0
    for ii in range(0, int(fs / CHUNK * temps_ecoute)):
        data = stream.read(CHUNK)
        data1 = np.frombuffer(data,dtype=np.int16)
        fft_data = (np.abs(np.fft.fft(data1)))
        Aplival = fft_data[int(frbit0*echelle)]
        Aplival2 = fft_data[int(frbit1*echelle)]
        if Aplival2 > Aplival and (Aplival2>Seuil_activation or Aplival>Seuil_activation):
            bitactuel = 1
        else:
            bitactuel = 0        
        if pas == 0:
            for i in range(0,len(bitetude)-1):
                bitetude[i] = bitetude[i+1]
            bitetude[len(bitetude)-1] = bitactuel
            if bitetude == code :
                stream.stop_stream()
                stream.close()
                audio.terminate()   
                return True         
        if pas == 9: # Pour prendre que un bit sur 10
            pas = 0
        else:
            pas = pas + 1        
        if ii == int(fs / CHUNK * temps_ecoute)-1:
            stream.stop_stream()
            stream.close()
            audio.terminate()  
            return False
        
def Emission_Reponse(Rep,frbit1,frbit0,fs,Baud_Rate): # Cette fonction emmet un tableau en audio pour la réponse
    Temps_par_bits = 1/Baud_Rate
    Données = Rep
    seconds = len(Données)*Temps_par_bits
    Données_multi = np.repeat(Données, seconds*fs/len(Données))
    t = np.linspace(0, seconds, int(seconds * fs), False)
    note = np.sin(frbit1 * t * 2 * np.pi)*Données_multi + np.sin(frbit0 * t * 2 * np.pi)*abs(Données_multi-1)
    audio = note * (2**15 - 1) / np.max(np.abs(note)) #Ensure that highest value is in 16-bit range
    audio = audio.astype(np.int16) #Convert to 16-bit data 
    play_obj = sa.play_buffer(audio, 1, 2, fs) #Start playback
    play_obj.wait_done()
Fr_bit0 = 800
Fr_bit1 = 1000
while True:
    x = input('Message : ')
    print("envoi de '",x, "' en cours ...")
    Emission_Message(x,Fr_bit0,Fr_bit1,44100,10,[0,1,1,1,0,1,0,1,0,1],[1,1,0,1,0,1,1,1,0,1])
    while Ecoute_Reponse([0,1,1,0,1],2,44100,300,Fr_bit0,Fr_bit1) == False:
        print("Aucune, réponse nouvelle tentative...")
        Emission_Message(x,Fr_bit0,Fr_bit1,44100,10,[0,1,1,1,0,1,0,1,0,1],[1,1,0,1,0,1,1,1,0,1])
    print("Message reçu")
