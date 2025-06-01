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

# Exibir clientes gerados
if "clientes" in st.session_state:
    st.subheader("Clientes Gerados")
    st.dataframe(pd.DataFrame(st.session_state["clientes"]))

    # ----------- PARTE 2: ALOCAR MESAS ----------- #
    st.header("2. Alocar Mesas (Interval Partitioning)")

    def alocar_mesas(clientes):
        clientes.sort(key=lambda x: x["chegada"])
        heap = []  # (fim, mesa_id)
        mesas = []

        for cliente in clientes:
            if heap and heap[0][0] <= cliente["chegada"]: #Se existe pelo menos uma mesa (heap) e o grupo que está para sair mais cedo (heap[0][0]) já terá saído até o horário de chegada do novo grupo (cliente["chegada"]), então essa mesa pode ser reutilizada para o novo grupo.
                _, mesa_id = heapq.heappop(heap)
            else:
                mesa_id = len(mesas) + 1 # Se não há mesas disponíveis, aloca uma nova mesa.
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
