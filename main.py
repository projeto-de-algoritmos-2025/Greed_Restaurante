import streamlit as st
import random
import heapq
import pandas as pd
import time # For time.sleep
from collections import Counter # Para contar as moedas

# --- Constantes ---
# Moedas de troco atualizadas para valores inteiros
MOEDAS_DISPONIVEIS = [100, 50, 20, 5, 1] # Em Reais

# --- Funções Auxiliares ---
def troco_guloso(valor_troco, moedas):
    """Calcula o troco usando um algoritmo guloso."""
    moedas_ordenadas = sorted(moedas, reverse=True)
    resultado_troco = []
    valor_restante = int(valor_troco) # Garantir que é inteiro

    for moeda in moedas_ordenadas:
        while valor_restante >= moeda and valor_restante > 0:
            resultado_troco.append(moeda)
            valor_restante -= moeda
    return resultado_troco

def formatar_troco(lista_moedas):
    """Formata a lista de moedas para a exibição desejada."""
    if not lista_moedas:
        return "Nenhuma moeda necessária."
    
    contagem_moedas = Counter(lista_moedas)
    # Ordenar pelas chaves (valor da moeda) em ordem decrescente para exibição
    partes_troco = []
    for moeda in sorted(contagem_moedas.keys(), reverse=True):
        quantidade = contagem_moedas[moeda]
        partes_troco.append(f"{quantidade}x R${moeda}")
    return ", ".join(partes_troco)


def alocar_mesas(clientes_input):
    """Aloca mesas aos clientes usando o algoritmo de Interval Partitioning."""
    if not clientes_input:
        return [], 0
    
    # Cria cópias para não modificar a lista original e ordena por chegada
    clientes_para_alocar = sorted([c.copy() for c in clientes_input], key=lambda x: x["chegada"])
    
    heap_mesas_ocupadas = []  # Armazena (tempo_saida_cliente, id_da_mesa)
    mesas_liberadas_ids = []  # Pilha (min-heap) de IDs de mesas que foram liberadas
    
    num_mesas_total_criadas = 0 
    clientes_com_mesa_atribuida = []

    for cliente in clientes_para_alocar:
        # Libera mesas que ficaram vagas antes ou no momento da chegada do cliente atual
        while heap_mesas_ocupadas and heap_mesas_ocupadas[0][0] <= cliente["chegada"]:
            _, mesa_id_que_liberou = heapq.heappop(heap_mesas_ocupadas)
            heapq.heappush(mesas_liberadas_ids, mesa_id_que_liberou) 
            
        if mesas_liberadas_ids:
            # Reutiliza uma mesa que foi liberada (a de menor ID, se houver várias)
            mesa_para_cliente = heapq.heappop(mesas_liberadas_ids)
        else:
            # Nenhuma mesa liberada disponível, cria uma nova
            num_mesas_total_criadas += 1
            mesa_para_cliente = num_mesas_total_criadas
            
        cliente["mesa"] = mesa_para_cliente
        heapq.heappush(heap_mesas_ocupadas, (cliente["saida"], mesa_para_cliente))
        clientes_com_mesa_atribuida.append(cliente)
        
    return clientes_com_mesa_atribuida, num_mesas_total_criadas

# --- Inicialização do Estado da Sessão ---
def inicializar_estado():
    """Inicializa todas as variáveis de estado necessárias."""
    default_states = {
        "clientes": [],
        "relogio": 0,
        "clientes_na_mesa": [],
        "cliente_pagando_atual": None,
        "clientes_finalizados": [],
        "simulacao_ativa": False,
        "troco_ideal_calculado_formatado": None, # Alterado para string formatada
        "mesas_utilizadas_total": 0,
        "log_eventos": ["Bem-vindo ao Simulador de Restaurante!"],
        "clientes_esperando_na_fila_pagamento": [] 
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

inicializar_estado()

# --- Interface do Usuário (UI) ---
st.set_page_config(page_title="Simulador de Restaurante Gulosos", layout="wide")
st.title("🍽️ Simulador de Restaurante com Algoritmos Gulosos (Valores Inteiros)")

# --- BARRA LATERAL ---
st.sidebar.header("1. Configurar Simulação")
num_clientes_input = st.sidebar.slider("Quantos grupos de clientes?", 3, 20, 7, key="num_clientes_slider")

if st.sidebar.button("Gerar Novos Clientes e Alocar Mesas"):
    clientes_gerados = []
    max_chegada_inicial = 5 
    for i in range(num_clientes_input):
        chegada = random.randint(0, max_chegada_inicial + i * 2) 
        duracao = random.randint(3, 8) 
        saida = chegada + duracao
        # Valores monetários agora são inteiros
        valor_conta = random.randint(25, 200) 
        
        # Gerar valor de pagamento oferecido pelo cliente de forma a tornar o troco mais variado/complexo
        # O 'troco_amount' é o valor exato do troco que será devido.
        
        prob_pagamento_exato = 0.05 # 5% de chance de pagamento exato
        if random.random() < prob_pagamento_exato:
            troco_amount = 0
        else:
            # 95% de chance de haver algum troco.
            # Gerar um valor de troco entre 1 e 39.
            # Este intervalo inclui valores que necessitam de uma única nota/moeda (1, 5, 20)
            # e muitos que necessitam de combinações (ex: 2, 3, 4, 6, 7, 13, 24, 37 etc.)
            troco_amount = random.randint(1, 39) 

        pagamento_oferecido = valor_conta + troco_amount

        clientes_gerados.append({
            "id": f"Grupo {chr(65+i)}",
            "chegada": chegada,
            "saida": saida,
            "valor_conta": valor_conta,
            "pagamento_oferecido": pagamento_oferecido,
            "mesa": None,
            "status": "aguardando"
        })
    
    # Reiniciar completamente o estado da simulação para um novo ciclo
    st.session_state.relogio = 0
    st.session_state.clientes_na_mesa = []
    st.session_state.cliente_pagando_atual = None
    st.session_state.clientes_finalizados = []
    st.session_state.simulacao_ativa = False # Crucial para parar o relógio automático
    st.session_state.troco_ideal_calculado_formatado = None
    st.session_state.clientes_esperando_na_fila_pagamento = []
    st.session_state.log_eventos = [f"Novos {len(clientes_gerados)} grupos de clientes gerados."] # Log reiniciado

    if clientes_gerados:
        clientes_com_mesas, num_mesas = alocar_mesas(clientes_gerados)
        st.session_state.clientes = clientes_com_mesas # Define a nova lista de clientes
        st.session_state.mesas_utilizadas_total = num_mesas
        st.session_state.log_eventos.append(f"Alocação de mesas completa: {num_mesas} mesas necessárias.")
    else:
        st.session_state.clientes = [] # Garante que a lista de clientes está vazia se nenhum for gerado
        st.session_state.mesas_utilizadas_total = 0
    st.rerun() # Força o Streamlit a re-executar o script com o estado resetado


st.sidebar.header("2. Controle da Simulação")
col1_control, col2_control = st.sidebar.columns(2)

pode_iniciar = not st.session_state.simulacao_ativa and not st.session_state.cliente_pagando_atual and st.session_state.clientes
if col1_control.button("▶️ Iniciar/Continuar", disabled=not pode_iniciar, use_container_width=True):
    st.session_state.simulacao_ativa = True
    st.session_state.log_eventos.append(f"Simulação iniciada/continuada no tempo {st.session_state.relogio}h.")
    st.rerun()

if col2_control.button("⏸️ Pausar", disabled=not st.session_state.simulacao_ativa, use_container_width=True):
    st.session_state.simulacao_ativa = False
    st.session_state.log_eventos.append(f"Simulação pausada no tempo {st.session_state.relogio}h.")
    st.rerun()

st.header(f"🕒 Relógio da Simulação: {st.session_state.relogio}h")

if st.session_state.clientes:
    with st.expander("📋 Fila de Clientes e Alocação Inicial de Mesas", expanded=False):
        df_display_clientes = pd.DataFrame(st.session_state.clientes)
        st.dataframe(df_display_clientes[["id", "chegada", "saida", "valor_conta", "pagamento_oferecido", "mesa", "status"]])
        st.info(f"Total de mesas que serão utilizadas na simulação: {st.session_state.mesas_utilizadas_total}")

col_info, col_pagamento = st.columns([0.6, 0.4])

with col_info:
    st.subheader("🪑 Clientes Atualmente nas Mesas")
    if st.session_state.clientes_na_mesa:
        df_mesas = pd.DataFrame(st.session_state.clientes_na_mesa)
        st.dataframe(df_mesas[["id", "mesa", "chegada", "saida", "valor_conta", "status"]])
    else:
        st.write("Nenhuma mesa ocupada no momento.")

    st.subheader("⏳ Clientes Aguardando para Sentar")
    clientes_aguardando_entrar = [
        c for c in st.session_state.clientes 
        if c["status"] == "aguardando" and c["chegada"] > st.session_state.relogio
    ]
    if clientes_aguardando_entrar:
         df_aguardando = pd.DataFrame(clientes_aguardando_entrar)
         st.dataframe(df_aguardando[["id", "chegada", "mesa", "status"]])
    else:
        st.write("Nenhum cliente aguardando para entrar ou todos já foram alocados.")

with col_pagamento:
    st.subheader("💸 Processamento de Pagamentos")
    cliente_pag = st.session_state.get("cliente_pagando_atual")

    if cliente_pag:
        st.warning(f"❗️ ATENÇÃO: Cliente {cliente_pag['id']} está pagando. Simulação PAUSADA.")
        st.markdown(f"**Cliente:** `{cliente_pag['id']}` (Mesa: {cliente_pag['mesa']})")
        st.markdown(f"**Valor da Conta:** `R$ {cliente_pag['valor_conta']}`")
        st.markdown(f"**Valor Oferecido:** `R$ {cliente_pag['pagamento_oferecido']}`")
        
        troco_devido = int(cliente_pag['pagamento_oferecido'] - cliente_pag['valor_conta'])
        
        if troco_devido < 0:
            st.error("ALERTA: Valor oferecido é INFERIOR à conta! Cliente precisa pagar mais.")
        elif troco_devido == 0:
            st.success("✅ Pagamento exato! Não é necessário troco.")
        else:
            st.markdown(f"**Troco a ser dado:** `R$ {troco_devido}`")
            if st.button(f"💰 Calcular Troco Ideal para {cliente_pag['id']}", key=f"calc_troco_{cliente_pag['id']}"):
                lista_moedas_troco = troco_guloso(troco_devido, MOEDAS_DISPONIVEIS)
                st.session_state.troco_ideal_calculado_formatado = formatar_troco(lista_moedas_troco)
                st.session_state.log_eventos.append(f"Troco ideal calculado para {cliente_pag['id']}: R${troco_devido}.")
                st.rerun() 

            if st.session_state.troco_ideal_calculado_formatado is not None:
                st.markdown("#### Troco Ideal (Menor qtd. de moedas/cédulas):")
                st.markdown(f"`{st.session_state.troco_ideal_calculado_formatado}`")

        
        if troco_devido >= 0:
            if st.button(f"✅ Confirmar Pagamento de {cliente_pag['id']} e Continuar Simulação", key=f"confirm_pag_{cliente_pag['id']}"):
                st.session_state.log_eventos.append(f"Pagamento de {cliente_pag['id']} (R${cliente_pag['valor_conta']}) confirmado.")
                
                for idx, c_main in enumerate(st.session_state.clientes):
                    if c_main["id"] == cliente_pag["id"]:
                        st.session_state.clientes[idx]["status"] = "finalizado"
                        break
                st.session_state.clientes_finalizados.append(cliente_pag)
                
                st.session_state.cliente_pagando_atual = None
                st.session_state.troco_ideal_calculado_formatado = None 
                
                if st.session_state.clientes_esperando_na_fila_pagamento:
                    proximo_a_pagar = st.session_state.clientes_esperando_na_fila_pagamento.pop(0)
                    st.session_state.cliente_pagando_atual = proximo_a_pagar
                    st.session_state.simulacao_ativa = False 
                    st.session_state.log_eventos.append(f"Cliente {proximo_a_pagar['id']} é o próximo a pagar. Simulação PAUSADA.")
                else:
                    if any(c['status'] != 'finalizado' for c in st.session_state.clientes): 
                         st.session_state.simulacao_ativa = True 
                         st.session_state.log_eventos.append("Todos os pagamentos pendentes resolvidos. Simulação retomada.")
                    else:
                        st.session_state.simulacao_ativa = False 
                        st.session_state.log_eventos.append("Todos os clientes finalizaram. Simulação concluída.")

                st.rerun()
    else:
        st.write("Nenhum cliente processando pagamento no momento.")

    st.subheader("🧾 Clientes que Concluíram o Pagamento")
    if st.session_state.clientes_finalizados:
        df_finalizados = pd.DataFrame(st.session_state.clientes_finalizados)
        st.dataframe(df_finalizados[["id", "mesa", "valor_conta", "pagamento_oferecido", "status"]])
    else:
        st.write("Nenhum cliente finalizou o pagamento ainda.")

# --- LÓGICA DA SIMULAÇÃO (AVANÇO DO RELÓGIO) ---
# Esta seção só executa se a simulação estiver ativa, não houver cliente pagando e houver clientes no sistema
if st.session_state.simulacao_ativa and not st.session_state.cliente_pagando_atual and st.session_state.clientes:
    time.sleep(1.0) # Ajuste a velocidade da simulação aqui (segundos)

    st.session_state.relogio += 1
    relogio_atual = st.session_state.relogio
    eventos_neste_tick = []

    # 1. Processar clientes chegando para sentar
    for idx, cliente in enumerate(st.session_state.clientes):
        if cliente["status"] == "aguardando" and cliente["chegada"] == relogio_atual:
            st.session_state.clientes[idx]["status"] = "sentado"
            st.session_state.clientes_na_mesa.append(st.session_state.clientes[idx])
            eventos_neste_tick.append(f"Cliente {cliente['id']} sentou-se à mesa {cliente['mesa']} no tempo {relogio_atual}h.")
    
    # 2. Processar clientes saindo da mesa para pagar
    clientes_que_sairam_neste_tick = []
    temp_clientes_na_mesa = list(st.session_state.clientes_na_mesa) 

    for cliente_na_mesa in temp_clientes_na_mesa:
        if cliente_na_mesa["status"] == "sentado" and cliente_na_mesa["saida"] == relogio_atual:
            # Atualiza status na lista principal de clientes
            for idx_main, c_main in enumerate(st.session_state.clientes):
                if c_main["id"] == cliente_na_mesa["id"]:
                    st.session_state.clientes[idx_main]["status"] = "pagando"
                    break
            
            st.session_state.clientes_na_mesa.remove(cliente_na_mesa) 
            st.session_state.clientes_esperando_na_fila_pagamento.append(cliente_na_mesa) 
            eventos_neste_tick.append(f"Cliente {cliente_na_mesa['id']} (mesa {cliente_na_mesa['mesa']}) levantou-se para pagar no tempo {relogio_atual}h.")
            clientes_que_sairam_neste_tick.append(cliente_na_mesa)

    # Se alguém saiu para pagar E não há ninguém pagando atualmente, define o primeiro da fila para pagar
    if clientes_que_sairam_neste_tick and not st.session_state.cliente_pagando_atual:
        if st.session_state.clientes_esperando_na_fila_pagamento:
            proximo_a_pagar = st.session_state.clientes_esperando_na_fila_pagamento.pop(0)
            st.session_state.cliente_pagando_atual = proximo_a_pagar
            st.session_state.simulacao_ativa = False # Pausa a simulação para o pagamento
            eventos_neste_tick.append(f"Cliente {proximo_a_pagar['id']} iniciando pagamento. Simulação PAUSADA.")

    if eventos_neste_tick:
        st.session_state.log_eventos.extend(eventos_neste_tick)
    
    # Verifica se todos os clientes terminaram
    todos_finalizados = all(c['status'] == 'finalizado' for c in st.session_state.clientes)
    if todos_finalizados and st.session_state.clientes: # Garante que há clientes para finalizar
        st.session_state.simulacao_ativa = False # Para a simulação
        st.session_state.log_eventos.append(f"Todos os {len(st.session_state.clientes)} clientes foram atendidos e pagaram. Simulação concluída no tempo {relogio_atual}h.")
        st.balloons() 

    st.rerun() # Roda o script novamente para atualizar a UI ou continuar o próximo tick se a simulação estiver ativa

# --- Log de Eventos na Barra Lateral ---
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Log de Eventos Recentes")
log_container = st.sidebar.container()
# Mostra os últimos N eventos, mais recentes no topo
for log_entry in reversed(st.session_state.log_eventos[-15:]): 
    log_container.caption(log_entry)

# --- Debug (opcional) ---
# if st.sidebar.checkbox("Mostrar Estado da Sessão (Debug)"):
#     st.sidebar.subheader("Debug State")
#     st.sidebar.json(st.session_state, expanded=False)
