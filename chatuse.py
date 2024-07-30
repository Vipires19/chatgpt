## Importando bibliotecas e criando o client
import os
import re
import openai
import streamlit as st
import pickle
from dotenv import load_dotenv,find_dotenv
from unidecode import unidecode
from pathlib import Path

pasta_mensagens = Path(__file__).parent / 'conversas_salvas'
pasta_mensagens.mkdir(exist_ok=True)
cache_desconverte = {}

client = openai.Client(api_key= st.secret['OPENAI_API_KEY'])

#################################################################################################################################
# Criando o chat

def resposta_chat(mensagens):
    respostas = client.chat.completions.create(
        messages = mensagens,
        model = 'gpt-3.5-turbo-0125',
        max_tokens = 1000,
        temperature = 0,
        stream = True,
    )           
    return respostas

#################################################################################################################################
#Salvando e lendo as convesar


def converte_nome(nome_mensagem):
    nome_arquivo = unidecode(nome_mensagem)
    nome_arquivo = re.sub('\W+', '', nome_arquivo).lower()
    return nome_arquivo

def desconverte_nome(nome_arquivo):
    if not nome_arquivo in cache_desconverte:
        nome_mensagem = ler_mensagem(nome_arquivo, key= 'nome_mensagem')
        cache_desconverte[nome_arquivo] = nome_mensagem
    return cache_desconverte[nome_arquivo]


def set_nome_msg(mensagens):
    nome_mensagem = ''
    for mensagem in mensagens:
        if mensagem['role'] == 'user':
            nome_mensagem = mensagem['content'][:30]
            break
    return nome_mensagem

def salva_mensagens(mensagens):
    if len(mensagens) == 0:
        return False
    nome_mensagem = set_nome_msg(mensagens)
    nome_arquivo = converte_nome(nome_mensagem)
    arquivo_salvar = {'nome_mensagem' : nome_mensagem, 
                      'nome_arquivo' : nome_arquivo,
                      'mensagens' : mensagens}
    with open(pasta_mensagens / nome_arquivo, 'wb') as f:
        pickle.dump(arquivo_salvar, f)

def ler_mensagem(nome_arquivo, key = 'mensagens'):
    with open(pasta_mensagens / nome_arquivo, 'rb') as f:
        mensagens = pickle.load(f)
    return mensagens[key]

def ler_arquivo(mensagens, key = 'mensagens'):
    if len(mensagens) == 0:
        return []
    nome_mensagem = set_nome_msg(mensagens)
    nome_arquivo = converte_nome(nome_mensagem)
    with open(pasta_mensagens / nome_arquivo, 'rb') as f:
        mensagens = pickle.load(f)
    return mensagens[key]

def listar_cvs():
    conversas = list(pasta_mensagens.glob('*'))
    conversas = sorted(conversas, key = lambda item: item.stat().st_mtime_ns, reverse=True)
    return [c.stem for c in conversas]

#################################################################################################################################
# Criando a página

def inicialização():
    if 'mensagens' not in st.session_state:
        st.session_state.mensagens = []
    if 'conversa_atual' not in st.session_state:
        st.session_state.conversa_atual = ''    

def pagina_principal():

    mensagens = ler_arquivo(st.session_state.mensagens)
    st.header('🤖 PirécoBot', divider = True)

    for mensagem in mensagens:
        chat = st.chat_message(mensagem['role'])
        chat.markdown(mensagem['content'])

    prompt = st.chat_input("Fale com o Piréco")
    if prompt:
        nova_mensagem = ({'role': 'user', 'content': prompt})
        chat = st.chat_message(nova_mensagem['role'])
        chat.markdown(nova_mensagem['content'])
        mensagens.append(nova_mensagem)
        st.session_state.mensagens = mensagens

        chat = st.chat_message('assistant')
        placeholder = chat.empty()
        placeholder.markdown('⎸')
        resposta_completa = ''
        respostas = resposta_chat(mensagens)
        for resposta in respostas:
            texto = resposta.choices[0].delta.content
            if texto:
                resposta_completa += texto
                print(texto, end = '')
            placeholder.markdown(resposta_completa + '⎸')
            placeholder.markdown(resposta_completa)
        nova_mensagem = {'role': 'assistant', 'content': resposta_completa}
        mensagens.append(nova_mensagem)
        
        st.session_state.mensagens = mensagens
        salva_mensagens(mensagens)

def tab_cvs(tab):
    tab.button('➕ Nova Conversa',
               on_click = seleciona_cvs,
                args = ('',),
                use_container_width = True)
    tab.markdown('')
    conversas = listar_cvs()
    for conversa in conversas:
        nome_mensagem = desconverte_nome(conversa).capitalize()
        if len(nome_mensagem) == 30:
            nome_mensagem += '...'
        tab.button(nome_mensagem,
                   on_click = seleciona_cvs,
                   args = (conversa, ),
                   disabled = conversa == st.session_state['conversa_atual'],
                   use_container_width = True)

def seleciona_cvs(nome_arquivo):
    if nome_arquivo == '':
        st.session_state.mensagens = []
    else:
        mensagens = ler_mensagem(nome_arquivo)
        st.session_state.mensagens = mensagens
    st.session_state['conversa_atual'] = nome_arquivo

def tab_cfg(tab):
    pass

def main():
    inicialização()
    pagina_principal()
    tab1,tab2 = st.sidebar.tabs(['Conversas', 'Configurações'])
    tab_cvs(tab1)
    tab_cfg(tab2)

if __name__ == '__main__':
    main()
