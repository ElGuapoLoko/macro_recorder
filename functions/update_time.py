import json

# valor inteiro desejado para todos os "t"
base_inteiro = 0  # 🔹 altere aqui ou peça via input()

input_file = "entrada.jsonl"
output_file = "saida.jsonl"

with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    for line in infile:
        data = json.loads(line)
        t = data["t"]

        # preserva apenas a parte decimal do original
        decimal = t - int(t)

        # monta o novo valor com o inteiro fixo
        data["t"] = round(base_inteiro + decimal, 6)

        json.dump(data, outfile)
        outfile.write("\n")

print(f"Processo concluído! Todos os 't' ajustados para iniciar em {base_inteiro}. Arquivo salvo como {output_file}")
