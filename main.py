import streamlit as st
import random
import heapq
import pandas as pd

st.set_page_config(page_title="Simulador de Restaurante Gulosos")
st.title("🍽️ Simulador de Restaurante com Algoritmos Gulosos")

# ----------- PARTE 1: GERAÇÃO DOS CLIENTES ----------- #
st.header("1. Gerar Grupos de Clientes")
num_clientes = st.slider("Quantos grupos de clientes?", 3, 15, 7)

if st.button("Gerar Clientes Aleatórios"):
    clientes = []
    for i in range(num_clientes):
        chegada = random.randint(10, 20)
        duracao = random.randint(1, 4)
        saida = chegada + duracao
        valor_conta = random.choice([37.5, 45.0, 56.0, 70.0, 87.0])
        pagamento = random.choice([50, 70, 100])
        clientes.append({
            "grupo": f"Grupo {chr(65+i)}",
            "chegada": chegada,
            "saida": saida,
            "valor_conta": valor_conta,
            "pagamento": pagamento
        })
    st.session_state["clientes"] = clientes
    st.session_state["relogio"] = 0
    st.session_state["clientes_na_mesa"] = []
    st.session_state["clientes_pagaram"] = []

# Exibir clientes gerados
if "clientes" in st.session_state:
    st.subheader("📋 Clientes Gerados")
    st.dataframe(pd.DataFrame(st.session_state["clientes"]))

    # ----------- PARTE 2: ALOCAR MESAS ----------- #
    st.header("2. Alocar Mesas (Interval Partitioning)")

    def alocar_mesas(clientes):
        clientes.sort(key=lambda x: x["chegada"])
        heap = []  # (fim, mesa_id)
        mesas = []

        for cliente in clientes:
            if heap and heap[0][0] <= cliente["chegada"]:
                _, mesa_id = heapq.heappop(heap)
            else:
                mesa_id = len(mesas) + 1
                mesas.append([])

            cliente["mesa"] = mesa_id
            mesas[mesa_id - 1].append(cliente)
            heapq.heappush(heap, (cliente["saida"], mesa_id))

        return clientes, mesas

    clientes_atualizados, mesas = alocar_mesas(st.session_state["clientes"])

    st.success(f"Total de mesas utilizadas: {len(mesas)}")
    df_clientes = pd.DataFrame(clientes_atualizados)
    st.dataframe(df_clientes.sort_values("mesa"))

    # Armazenar para próxima etapa
    st.session_state["clientes"] = clientes_atualizados
    st.session_state["mesas"] = mesas

    # ----------- PARTE 3: SIMULAÇÃO DO RELÓGIO ----------- #
    st.header("3. Simulação de Funcionamento (Relógio)")

    if st.button("⏱️ Avançar 1 minuto"):
        st.session_state["relogio"] += 1
        relogio = st.session_state["relogio"]
        novos = [c for c in st.session_state["clientes"] if c["chegada"] == relogio]
        saindo = [c for c in st.session_state["clientes_na_mesa"] if c["saida"] == relogio]

        for c in novos:
            st.session_state["clientes_na_mesa"].append(c)

        for c in saindo:
            st.session_state["clientes_pagaram"].append(c)
            st.session_state["clientes_na_mesa"].remove(c)

    st.subheader(f"🕒 Horário atual: {st.session_state['relogio']}h")

    st.markdown("### 🪑 Clientes sentados")
    if st.session_state["clientes_na_mesa"]:
        st.table(pd.DataFrame(st.session_state["clientes_na_mesa"]))
    else:
        st.write("Nenhum cliente está sentado no momento.")

    st.markdown("### 💸 Clientes prontos para pagar")
    for cliente in st.session_state["clientes_pagaram"]:
        with st.expander(f"{cliente['grupo']} (Conta: R$ {cliente['valor_conta']} | Pagou: R$ {cliente['pagamento']})"):
            troco = round(cliente["pagamento"] - cliente["valor_conta"], 2)
            st.write(f"Troco devido: R$ {troco:.2f}")

            moedas_usuario = st.text_input(f"Moedas oferecidas por {cliente['grupo']} (separe por vírgula)", key=cliente['grupo'])

            def troco_guloso(valor, moedas):
                moedas.sort(reverse=True)
                resultado = []
                for moeda in moedas:
                    while round(valor - moeda, 2) >= 0:
                        valor = round(valor - moeda, 2)
                        resultado.append(moeda)
                return resultado

            if moedas_usuario:
                try:
                    entrada = list(map(float, moedas_usuario.split(",")))
                    soma = round(sum(entrada), 2)

                    if soma != troco:
                        st.error(f"❌ Troco incorreto. Você deu R$ {soma:.2f}, mas deveria ser R$ {troco:.2f}.")
                    else:
                        ideal = troco_guloso(troco, [1.0, 0.5, 0.25, 0.1, 0.05])
                        if len(entrada) == len(ideal):
                            st.success("✅ Perfeito! Você usou o número mínimo de moedas.")
                        else:
                            st.warning(f"⚠️ Troco correto, mas você usou {len(entrada)} moedas. O ideal seria {len(ideal)}.")
                except:
                    st.error("Erro ao interpretar as moedas. Use vírgulas e apenas números válidos.")
