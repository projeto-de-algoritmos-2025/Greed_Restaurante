import streamlit as st
import random
import heapq
import pandas as pd
import time
from collections import Counter
import copy

# --- Constantes ---
MOEDAS_DISPONIVEIS = [100, 50, 20, 5, 1]  # Em Reais

# --- Funções Auxiliares ---
def troco_guloso(valor_troco, moedas):
    """Calcula o troco usando um algoritmo guloso."""
    moedas_ordenadas = sorted(moedas, reverse=True)
    resultado_troco = []
    valor_restante = int(valor_troco)
    for moeda in moedas_ordenadas:
        while valor_restante >= moeda:
            resultado_troco.append(moeda)
            valor_restante -= moeda
    return resultado_troco

def formatar_troco(lista_moedas):
    """Formata a lista de moedas para a exibição desejada."""
    if not lista_moedas:
        return "Nenhuma moeda necessária."
    contagem_moedas = Counter(lista_moedas)
    return ", ".join(
        f"{contagem_moedas[moeda]}x R${moeda}"
        for moeda in sorted(contagem_moedas.keys(), reverse=True)
    )

def alocar_mesas(clientes_input):
    """Aloca mesas aos clientes usando o algoritmo de Interval Partitioning."""
    if not clientes_input:
        return [], 0
    clientes_para_alocar = sorted([copy.deepcopy(c) for c in clientes_input], key=lambda x: x["chegada"])
    heap_mesas_ocupadas = []
    mesas_liberadas_ids = []
    num_mesas_total_criadas = 0
    clientes_com_mesa_atribuida = []
    for cliente in clientes_para_alocar:
        while heap_mesas_ocupadas and heap_mesas_ocupadas[0][0] <= cliente["chegada"]:
            _, mesa_id_que_liberou = heapq.heappop(heap_mesas_ocupadas)
            heapq.heappush(mesas_liberadas_ids, mesa_id_que_liberou)
        if mesas_liberadas_ids:
            mesa_para_cliente = heapq.heappop(mesas_liberadas_ids)
        else:
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
        "troco_ideal_calculado_formatado": None,
        "mesas_utilizadas_total": 0,
        "log_eventos": ["Bem-vindo ao Simulador de Restaurante!"],
        "clientes_esperando_na_fila_pagamento": []
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

inicializar_estado()

# --- Interface do Usuário (UI) ---
st.set_page_config(page_title="Simulador de Restaurante Ambiciosos", layout="wide")
st.title("🍽️ Simulador de Restaurante com Algoritmos Ambiciosos")

# --- BARRA LATERAL ---
st.sidebar.header("1. Configurar Simulação")
num_clientes_input = st.sidebar.slider("Quantos grupos de clientes?", 3, 20, 7, key="num_clientes_slider")

if st.sidebar.button("Gerar Novos Clientes e Alocar Mesas"):
    max_chegada_inicial = 5
    prob_pagamento_exato = 0.05
    clientes_gerados = [
        {
            "id": f"Grupo {chr(65+i)}",
            "chegada": (chegada := random.randint(0, max_chegada_inicial + i * 2)),
            "saida": (saida := chegada + random.randint(3, 8)),
            "valor_conta": (valor_conta := random.randint(25, 200)),
            "pagamento_oferecido": valor_conta + (troco_amount := 0 if random.random() < prob_pagamento_exato else random.randint(1, 39)),
            "mesa": None,
            "status": "aguardando"
        }
        for i in range(num_clientes_input)
    ]
    st.session_state.relogio = 0
    st.session_state.clientes_na_mesa = []
    st.session_state.cliente_pagando_atual = None
    st.session_state.clientes_finalizados = []
    st.session_state.simulacao_ativa = False
    st.session_state.troco_ideal_calculado_formatado = None
    st.session_state.clientes_esperando_na_fila_pagamento = []
    st.session_state.log_eventos = [f"Novos {len(clientes_gerados)} grupos de clientes gerados."]
    if clientes_gerados:
        clientes_com_mesas, num_mesas = alocar_mesas(clientes_gerados)
        st.session_state.clientes = clientes_com_mesas
        st.session_state.mesas_utilizadas_total = num_mesas
        st.session_state.log_eventos.append(f"Alocação de mesas completa: {num_mesas} mesas necessárias.")
    else:
        st.session_state.clientes = []
        st.session_state.mesas_utilizadas_total = 0
    st.rerun()

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

                # Tentativa de atualizar o status do cliente para finalizado
                cliente_finalizado_id = cliente_pag["id"]
                cliente_encontrado_para_finalizar = False
                for idx, c_main in enumerate(st.session_state.clientes):
                    if c_main["id"] == cliente_finalizado_id:
                        st.session_state.clientes[idx]["status"] = "finalizado"
                        cliente_encontrado_para_finalizar = True
                        break
                if not cliente_encontrado_para_finalizar:
                    st.session_state.log_eventos.append(f"DEBUG ERRO: Cliente {cliente_finalizado_id} NÃO FOI ENCONTRADO na lista st.session_state.clientes para finalizar.")
                st.session_state.clientes_finalizados.append(cliente_pag) # Adiciona à lista de finalizados (que é uma cópia)
                st.session_state.cliente_pagando_atual = None
                st.session_state.troco_ideal_calculado_formatado = None
                # --- INÍCIO DO BLOCO DE DEPURAÇÃO ---
                log_detalhado_clientes = []
                status_do_cliente_que_pagou_na_lista_principal = "NÃO ENCONTRADO APÓS PAGAMENTO"
                for c_debug in st.session_state.clientes:
                    log_detalhado_clientes.append(
                        f"ID: {c_debug['id']}, Status: {c_debug['status']}, "
                        f"Chegada: {c_debug.get('chegada', 'N/A')}, Saida: {c_debug.get('saida', 'N/A')}"
                    )
                    if c_debug['id'] == cliente_finalizado_id:
                        status_do_cliente_que_pagou_na_lista_principal = c_debug['status']
                # --- FIM DO BLOCO DE DEPURAÇÃO ---
                if st.session_state.clientes_esperando_na_fila_pagamento:
                    proximo_a_pagar = st.session_state.clientes_esperando_na_fila_pagamento.pop(0)
                    st.session_state.cliente_pagando_atual = proximo_a_pagar
                    st.session_state.simulacao_ativa = False
                    st.session_state.log_eventos.append(f"Cliente {proximo_a_pagar['id']} é o próximo a pagar. Simulação PAUSADA.")
                else:
                    # A decisão de continuar ou parar a simulação é feita aqui
                    if any(c['status'] != 'finalizado' for c in st.session_state.clientes):
                        st.session_state.simulacao_ativa = True
                        st.session_state.log_eventos.append(f"Ainda há clientes não finalizados. Simulação retomada.")
                    else:
                        st.session_state.simulacao_ativa = False
                        st.session_state.log_eventos.append(f"Todos os clientes finalizaram. Simulação concluída.")

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
if st.session_state.simulacao_ativa and not st.session_state.cliente_pagando_atual and st.session_state.clientes:
    # Define o tempo atual para processar eventos DESTE tick
    relogio_para_eventos_deste_tick = st.session_state.relogio
    eventos_neste_tick = []

    # 1. Processar clientes chegando para sentar
    for idx, cliente in enumerate(st.session_state.clientes):
        if cliente["status"] == "aguardando" and cliente["chegada"] == relogio_para_eventos_deste_tick:
            st.session_state.clientes[idx]["status"] = "sentado"
            st.session_state.clientes_na_mesa.append(st.session_state.clientes[idx])
            eventos_neste_tick.append(f"Cliente {cliente['id']} sentou-se à mesa {cliente['mesa']} no tempo {relogio_para_eventos_deste_tick}h.")

    # 2. Processar clientes saindo da mesa para pagar
    clientes_que_sairam_neste_tick = []
    temp_clientes_na_mesa = list(st.session_state.clientes_na_mesa) # Cópia para iterar
    for cliente_na_mesa in temp_clientes_na_mesa:
        if cliente_na_mesa["status"] == "sentado" and cliente_na_mesa["saida"] == relogio_para_eventos_deste_tick:
            for idx_main, c_main in enumerate(st.session_state.clientes):
                if c_main["id"] == cliente_na_mesa["id"]:
                    st.session_state.clientes[idx_main]["status"] = "pagando"
                    break
            st.session_state.clientes_na_mesa.remove(cliente_na_mesa) # Remover o objeto original
            st.session_state.clientes_esperando_na_fila_pagamento.append(cliente_na_mesa)
            eventos_neste_tick.append(f"Cliente {cliente_na_mesa['id']} (mesa {cliente_na_mesa['mesa']}) levantou-se para pagar no tempo {relogio_para_eventos_deste_tick}h.")
            clientes_que_sairam_neste_tick.append(cliente_na_mesa)

    # Se algum cliente saiu para pagar E o caixa está livre, processa o primeiro da fila
    if clientes_que_sairam_neste_tick and not st.session_state.cliente_pagando_atual:
        if st.session_state.clientes_esperando_na_fila_pagamento:
            proximo_a_pagar = st.session_state.clientes_esperando_na_fila_pagamento.pop(0)
            st.session_state.cliente_pagando_atual = proximo_a_pagar
            st.session_state.simulacao_ativa = False # Pausa para pagamento
            eventos_neste_tick.append(f"Cliente {proximo_a_pagar['id']} iniciando pagamento. Simulação PAUSADA.")

    if eventos_neste_tick:
        st.session_state.log_eventos.extend(eventos_neste_tick)

    # Verifica se todos os clientes foram finalizados APÓS os eventos do tick atual
    todos_finalizados = all(c['status'] == 'finalizado' for c in st.session_state.clientes)
    if todos_finalizados and st.session_state.clientes:
        st.session_state.simulacao_ativa = False
        st.session_state.log_eventos.append(f"Todos os {len(st.session_state.clientes)} clientes foram atendidos e pagaram. Simulação concluída no tempo {relogio_para_eventos_deste_tick}h.")
        st.balloons()
    else:
        # Se a simulação não terminou e não foi pausada para pagamento, avança para o próximo tick.
        if st.session_state.simulacao_ativa:
            time.sleep(1.0) # Mova o sleep para cá, para que ocorra apenas se a simulação for continuar
            st.session_state.relogio += 1 # INCREMENTA O RELÓGIO PARA O PRÓXIMO TICK

    st.rerun()

# --- Log de Eventos na Barra Lateral ---
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Log de Eventos Recentes")
log_container = st.sidebar.container()
for log_entry in reversed(st.session_state.log_eventos[-15:]):
    log_container.caption(log_entry)


