import json

base = 1330

input_file = "entrada.jsonl"
output_file = "saida.jsonl"

with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    for line in infile:
        data = json.loads(line)
        t = data["t"]

        # separa parte inteira e decimal
        inteiro = int(t)
        decimal = t - inteiro

        # soma o inteiro original à base
        data["t"] = round(base + inteiro + decimal, 6)

        json.dump(data, outfile)
        outfile.write("\n")

print(f"Processo concluído! Valores de 't' iniciando em {base}. Arquivo salvo como {output_file}")
