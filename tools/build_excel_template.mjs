import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workspace = "D:/00-proyectos-personales/recaudacion-conteo";
const outputPath = path.join(workspace, "templates", "plantilla-carga-recaudacion.xlsx");
const previewPath = path.join(workspace, "artifacts", "previews", "plantilla-carga-recaudacion.png");

const concepts = [
  ["INM", "INMOBILIARIO"],
  ["AUT", "AUTOMOTOR"],
  ["IIBB_LOC", "II.BB (Local)"],
  ["IIBB_RS", "II.BB. (Reg. Simplificado)"],
  ["IIBB_RET", "II.BB. (Retención)"],
  ["IIBB_PER", "II.BB. (Percepción)"],
  ["IIBB_RET_CM", "II.BB. (RET. C.M.)"],
  ["IIBB_PER_CM", "II.BB. (PERCEP. C.M.)"],
  ["IIBB_CM", "II.BB. (Conv. Multil.)"],
  ["IIBB_ARB", "II.BB. (Ag.Rec.B.)"],
  ["IIBB_SIRCREB", "II.BB. (Sircreb)"],
  ["SEL", "SELLOS"],
  ["AG_SEL", "AG. DE SELLOS"],
  ["TRS", "TASA RETRIBUTIVA"],
  ["OTROS", "Otros"],
];

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Detalle");
sheet.showGridLines = false;
sheet.tabColor = "#17365D";

sheet.getRange("A2:H2").merge();
sheet.getRange("A2").values = [["Carga de recaudación por concepto"]];
sheet.getRange("A2:H2").format = {
  font: { name: "Arial", size: 15, bold: true, color: "#17365D" },
  verticalAlignment: "center",
};
sheet.getRange("A2:H2").format.rowHeight = 26;

sheet.getRange("A3:H3").format.borders = {
  bottom: { style: "thin", color: "#7F8C8D" },
};

sheet.getRange("A4:H4").merge();
sheet.getRange("A4").values = [[
  "Complete únicamente las celdas amarillas. Canal, fecha de recaudación y fecha de ingreso a TGP se informan en la aplicación.",
]];
sheet.getRange("A4:H4").format = {
  font: { name: "Arial", size: 10, italic: true, color: "#404040" },
  fill: "#FFF2CC",
  wrapText: true,
  verticalAlignment: "center",
};
sheet.getRange("A4:H4").format.rowHeight = 34;

sheet.getRange("A5:H5").merge();
sheet.getRange("A5").values = [[
  "Use cero cuando un concepto no tenga movimientos. No cambie códigos, nombres ni encabezados.",
]];
sheet.getRange("A5:H5").format = {
  font: { name: "Arial", size: 10, color: "#666666" },
  verticalAlignment: "center",
};

const headers = [[
  "CODIGO_CONCEPTO",
  "CONCEPTO",
  "CANTIDAD_COMPROBANTES",
  "RECAUDACION_BRUTA",
  "COMISION",
  "IVA_COMISION",
  "OTROS_GASTOS",
  "OBSERVACIONES",
]];
sheet.getRange("A7:H7").values = headers;
sheet.getRange("A7:H7").format = {
  fill: "#17365D",
  font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
};
sheet.getRange("A7:H7").format.rowHeight = 34;

const rows = concepts.map(([code, name]) => [code, name, 0, 0, 0, 0, 0, ""]);
sheet.getRange("A8:H22").values = rows;
sheet.getRange("A8:H22").format = {
  font: { name: "Arial", size: 10, color: "#222222" },
  verticalAlignment: "center",
  borders: {
    insideHorizontal: { style: "thin", color: "#D9E2F3" },
    bottom: { style: "thin", color: "#A6A6A6" },
  },
};
sheet.getRange("A8:B22").format.fill = "#E7E6E6";
sheet.getRange("A8:B22").format.font = { name: "Arial", size: 10, bold: true, color: "#404040" };
sheet.getRange("C8:H22").format.fill = "#FFF2CC";
sheet.getRange("C8:C22").format.numberFormat = "#,##0";
sheet.getRange("D8:G22").format.numberFormat = "$#,##0.00";
sheet.getRange("C8:G22").format.horizontalAlignment = "right";
sheet.getRange("H8:H22").format.wrapText = false;
sheet.getRange("A8:H22").format.rowHeight = 22;

sheet.dataValidations.add({
  range: "C8:C22",
  rule: { type: "whole", operator: "between", formula1: 0, formula2: 2147483647 },
});
for (const range of ["D8:D22", "E8:E22", "F8:F22", "G8:G22"]) {
  sheet.dataValidations.add({
    range,
    rule: { type: "decimal", operator: "between", formula1: 0, formula2: 999999999999999.99 },
  });
}

sheet.getRange("A24:B24").merge();
sheet.getRange("A24").values = [["TOTAL DE CONTROL"]];
sheet.getRange("C24").formulas = [["=SUM(C8:C22)"]];
sheet.getRange("D24").formulas = [["=SUM(D8:D22)"]];
sheet.getRange("E24").formulas = [["=SUM(E8:E22)"]];
sheet.getRange("F24").formulas = [["=SUM(F8:F22)"]];
sheet.getRange("G24").formulas = [["=SUM(G8:G22)"]];
sheet.getRange("A24:G24").format = {
  fill: "#D9EAD3",
  font: { name: "Arial", size: 10, bold: true, color: "#274E13" },
  borders: { preset: "outside", style: "thin", color: "#6AA84F" },
  verticalAlignment: "center",
};
sheet.getRange("C24").format.numberFormat = "#,##0";
sheet.getRange("D24:G24").format.numberFormat = "$#,##0.00";

sheet.getRange("A25:C25").merge();
sheet.getRange("A25").values = [["RECAUDACIÓN NETA CALCULADA"]];
sheet.getRange("D25").formulas = [["=D24-E24-F24"]];
sheet.getRange("A25:D25").format = {
  fill: "#D9EAD3",
  font: { name: "Arial", size: 10, bold: true, color: "#274E13" },
  borders: { preset: "outside", style: "thin", color: "#6AA84F" },
};
sheet.getRange("D25").format.numberFormat = "$#,##0.00";

sheet.getRange("A27:H27").merge();
sheet.getRange("A27").values = [[
  "La aplicación recalcula y valida todos los totales. Esta sección es únicamente un control visual y no se importa.",
]];
sheet.getRange("A27:H27").format = {
  font: { name: "Arial", size: 9, italic: true, color: "#666666" },
};

sheet.getRange("A1:H27").format.verticalAlignment = "center";
sheet.getRange("A1:A27").format.columnWidth = 18;
sheet.getRange("B1:B27").format.columnWidth = 31;
sheet.getRange("C1:C27").format.columnWidth = 22;
sheet.getRange("D1:G27").format.columnWidth = 20;
sheet.getRange("H1:H27").format.columnWidth = 32;
sheet.freezePanes.freezeRows(7);
sheet.freezePanes.freezeColumns(2);

const table = sheet.tables.add("A7:H22", true, "DetalleRecaudacion");
table.style = "TableStyleMedium2";
table.showBandedRows = false;
table.showFilterButton = true;

workbook.recalculate();

const inspection = await workbook.inspect({
  kind: "table",
  range: "Detalle!A7:H25",
  include: "values,formulas",
  tableMaxRows: 25,
  tableMaxCols: 8,
  maxChars: 12000,
});
console.log(inspection.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(path.dirname(previewPath), { recursive: true });
const preview = await workbook.render({ sheetName: "Detalle", range: "A1:H27", scale: 1.25, format: "png" });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

console.log(JSON.stringify({ outputPath, previewPath }));
