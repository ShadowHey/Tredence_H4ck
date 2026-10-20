import { toPng } from "html-to-image";

export async function exportElementAsPng(elementId: string, filename: string): Promise<void> {
  const node = document.getElementById(elementId);
  if (!node) {
    throw new Error(`Element with id "${elementId}" not found for visual export.`);
  }

  try {
    const dataUrl = await toPng(node, {
      backgroundColor: "#ffffff",
      quality: 0.95,
      pixelRatio: 2, // High resolution for clear dimension lines and text
    });

    const link = document.createElement("a");
    link.download = filename.endsWith(".png") ? filename : `${filename}.png`;
    link.href = dataUrl;
    link.click();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("Visual export failed:", err);
    throw new Error(`Failed to generate PNG export: ${message}`);
  }
}

export function downloadJsonFile(data: object, filename: string): void {
  const jsonStr = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.download = filename.endsWith(".json") ? filename : `${filename}.json`;
  link.href = url;
  link.click();
  URL.revokeObjectURL(url);
}
