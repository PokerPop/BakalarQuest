# -*- coding: utf-8 -*-
import socket
from threading import Thread, Lock
from BakalarQuestStrukture import Igrac, Soba
import db
import os

#During handling of the above exception, another exception occurred:

lista_veza = list() #lista veza; koristi se za slanje poruka svim klijentima
lista_adresa = list() #lista adresa veze, sadrzi samo id adrese/veze
svijet = list()
lock = Lock() #koristi se za rad s globalnim varijablima

def prekid_veze(veza, adresa):
    veza.send("Prekidam vezu...\n")
    print("Prekidam vezu s", adresa[0])
    lock.acquire()
    for j in range(len(lista_veza)):
        if lista_adresa[j] == adresa[1]:
            lista_adresa.pop(j)
            lista_veza.pop(j)#micanje veze iz lista veza
            break
    lock.release()
    veza.close()#prekidanje veze

def prerada_poruke(poruka):
    poruka = poruka.split()#Rastavi na rijeci. Ovo treba jer mice new line
    if len(poruka) < 1:
        return "ERROR: Nemoj spamat!\n"
    else:
        poruka = ' '.join(poruka)#sastavi rijeci natrag u "recenicu"
        return poruka


def odvajanje(poruka, adrs): #funkcija koja mice komandu i stavlja ip adresu umjesto toga
    poruka = poruka.split()
    poruka[0] = adrs[0] + ':'
    poruka = ' '.join(poruka)
    poruka = poruka + '\n'
    return poruka

def komunikacija(veza,adresa):
    BUFFER_SIZE = 1024 #buffer za primljene podataka
    veza.send("Dobrodosli u BakalarQuest!\nAko se zelite prijaviti, upisite '/prijavi [korisnicko_ime] [password]'.\nAko zelite se napraviti novi racun, upisite '/kreiraj' i pratite korake.\nAko zelite izaci, upisite '/izlaz'.\n")
    bool_i = 0
    bool_k = 0
    while bool_i != 1:
        data = veza.recv(BUFFER_SIZE)
        data = prerada_poruke(data)
        if data.split()[0] == "/prijavi" and len(data.split()) == 3:
            veza.send("Spojeni ste!\n")
            bool_i = 1
        elif data == "/kreiraj":
            while bool_i != 1:
                if bool_k == 0:
                    veza.send("Upisite novo korisnicko ime: ")
                    data = veza.recv(BUFFER_SIZE)
                    data = prerada_poruke(data)
                    if len(data.split())!=1 and bool_k == 0:
                        veza.send("Korisnicko ime mora biti jedna rijec, bez razmaka!\n") 
                        continue
                    else:
                        bool_k = 1
                veza.send("Upisite lozinku: ")
                data = veza.recv(BUFFER_SIZE)
                data = prerada_poruke(data)
                if len(data.split())!=1:
                    veza.send("Lozinka mora biti jedna rijec, bez razmaka!\n")
                    continue
                else:
                    bool_i = 1
        elif data == "/izlaz":
            prekid_veze(veza, adresa)
            return
        elif data.split()[0] == "ERROR:":
            veza.send(data)
        else:
            veza.send("Ovo kaj si napisali nema smisla...\n")
    
    while 1:
        data = "/pomoc ->  prikazuje ovaj tekst\n/izlaz ->  prekida vezu s serverom\n/reci [poruka] ->  Saljes poruku ostalim igracima\n/ponovi [poruka] ->  ponovi poslanu poruku\n"
        veza.send(data)
        data = veza.recv(BUFFER_SIZE)#primi paket
        data = prerada_poruke(data)
        if data.split()[0] == "ERROR:":
            veza.send(data)
        elif data == "/izlaz":
            prekid_veze(veza, adresa)
            return
        elif data == "/server shutdown":
            print("Gasim server.")
            os._exit(1)#gasi sve dretve i izlazi iz programa
        elif data.split()[0] == "/reci":
            data = odvajanje(data, adresa)
            print("Saljem poruku svim klijentima osim source:",data)
            lock.acquire()
            for j in range(len(lista_veza)):
                lista_veza[j].send(data)
            lock.release()#ova petlja salje svima poruku osim izvoru koji je poslao poruku
        elif data.split()[0] == "/ponovi":
            data = odvajanje(data, adresa)
            print("Vracam poruku:",data)
            veza.send(data)#vraca istu poruku koji je klijent poslao
        elif data == "/pomoc":
            data = "/pomoc ->  prikazuje ovaj tekst\n/izlaz ->  prekida vezu s serverom\n/reci [poruka] ->  Saljes poruku ostalim igracima\n/ponovi [poruka] ->  ponovi poslanu poruku\n"
            veza.send(data)
        else:
            veza.send("Ovo kaj si napisali nema smisla...\n")
            

TCP_IP = "127.0.0.1"
#TCP_IP = "161.53.120.19"
TCP_PORT = 8880

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(50) #otvaranje veze

svijet = db.connect_db()
for j in range(len(svijet)):
    for l in range(len(svijet[j])):
        svijet[j][l] = svijet[j][l].encode('utf-8')

print("Server je startan.")

while 1:
    conn, addr = s.accept() #prihvacanje veze
    print("Klijent spojen: ", addr) #prikazuje tko se spojio
    lock.acquire()
    lista_veza.append(conn) #dodaju se inf o vezi
    lista_adresa.append(addr[1])
    lock.release()
    kom_veza = Thread(target=komunikacija, args=(conn,addr,))#definiranje dretve
    kom_veza.setDaemon(True)
    kom_veza.start()#zapocinje dretvu
