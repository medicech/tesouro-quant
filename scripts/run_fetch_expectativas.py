from core.datasources.bcb_expectativas import fetch_expectativas_anuais, latest_expectativas_snapshot
from core.expectativas import append_expectativas_history
from core.config import PROCESSED_DIR


def main():
    anos = list(range(2026, 2046))  # 2026..2035
    df = fetch_expectativas_anuais(indicadores=["Selic", "IPCA"], anos=anos)

    data_ref, snap = latest_expectativas_snapshot(df)
    if snap.empty:
        print("Sem dados retornados do BCB.")
        return

    out = PROCESSED_DIR / f"expectativas_snapshot_{data_ref.date().isoformat()}.parquet"
    snap.to_parquet(out, index=False)

    hist_path = append_expectativas_history(df)

    print("Data ref (snapshot):", data_ref.date())
    print("Linhas snapshot:", len(snap))
    print("Anos no snapshot:", sorted(snap["ano"].unique().tolist()))
    print("Arquivo salvo:", out)
    print("Histórico atualizado:", hist_path)
    print(snap.head(20))


if __name__ == "__main__":
    main()
