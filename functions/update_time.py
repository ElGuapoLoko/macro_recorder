import json

incremento = 10

input_file = "entrada.jsonl"
output_file = "saida.jsonl"

with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    for line in infile:
        data = json.loads(line)
        t = data["t"]

        inteiro = int(t)
        decimal = t - inteiro

        # soma o valor informado na variável "incremento"
        novo_t = (inteiro + incremento) + decimal

        # arredonda para 6 casas decimais
        data["t"] = round(novo_t, 6)

        json.dump(data, outfile)
        outfile.write("\n")

print(f"Processo concluído! +{incremento} aplicado a cada 't'. Arquivo salvo como {output_file}")
