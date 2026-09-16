/** Formatacao numerica no padrao brasileiro.
 *
 * A interface mistura contagens (4.096 qubits, ponto como separador de milhar)
 * com fracoes (26,3%, 1,60 s). Sem um formatador unico, `toFixed` produz ponto
 * decimal ao lado de ponto de milhar — e "1.60 s" passa a ser lido como 160.
 */
const cache = new Map<number, Intl.NumberFormat>();

function formatter(digits: number): Intl.NumberFormat {
  let format = cache.get(digits);
  if (!format) {
    format = new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
    cache.set(digits, format);
  }
  return format;
}

/** Numero com casas decimais fixas: `formatNumber(1.6, 2)` -> "1,60". */
export function formatNumber(value: number, digits = 0): string {
  return formatter(digits).format(value);
}

/** Fracao como porcentagem: `formatPercent(0.263)` -> "26,3%". */
export function formatPercent(fraction: number, digits = 1): string {
  return `${formatter(digits).format(fraction * 100)}%`;
}
