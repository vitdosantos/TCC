#!/bin/bash

# --- CONFIGURACOES ---
# IP do Samba AD DC (Onde esta o DNS)
NS="172.16.0.10"
# Nome do seu dominio
ZONE="vme.solutions"
# Tempo de vida do registro
TTL="300"

# --- VARIAVEIS DO DHCP ---
action=$1
ip=$2
name=$3

# --- AJUSTA O NOME ---
# Pega so o primeiro nome (ex: pc1) e adiciona o dominio
hostname=$(echo "$name" | cut -d. -f1)
fqdn="${hostname}.${ZONE}"

# Arquivo temporario para os comandos
tmpfile=$(mktemp)

# --- CRIA O COMANDO PRO NSUPDATE ---
# Note que NAO tem autenticacao (sem kinit, sem keytab)
if [ "$action" = "add" ]; then
    echo "server $NS" > $tmpfile
    echo "update delete $fqdn A" >> $tmpfile
    echo "update add $fqdn $TTL A $ip" >> $tmpfile
    echo "send" >> $tmpfile
elif [ "$action" = "delete" ]; then
    echo "server $NS" > $tmpfile
    echo "update delete $fqdn A" >> $tmpfile
    echo "send" >> $tmpfile
fi

# --- ENVIA ---
# O -v mostra o resultado no log
nsupdate -v "$tmpfile"
result=$?

rm -f "$tmpfile"
exit $result
