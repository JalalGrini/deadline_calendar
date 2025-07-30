import streamlit as st

def show_invoice_calculator():
    st.subheader("🧾 Invoice Calculator (Excl. VAT ➜ Incl. VAT)")
    col1, col2 = st.columns(2)
    with col1:
        ht = st.number_input("💵 Montant HT", min_value=0.0, format="%.2f", step=100.0)
    with col2:
        tva_rate = st.number_input("📊 Taux TVA (%)", min_value=0.0, max_value=100.0, value=20.0, format="%.2f")

    if ht > 0:
        tva_amount = ht * tva_rate / 100
        ttc = ht + tva_amount
        st.success(f"**Montant TVA :** {tva_amount:.2f} MAD")
        st.success(f"**Montant TTC :** {ttc:.2f} MAD")
    else:
        st.info("Entrez un montant HT pour calculer le TTC.")