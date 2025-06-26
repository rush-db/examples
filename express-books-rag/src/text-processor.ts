import { pipeline } from '@xenova/transformers';

const extractors = new Map<string, any>();

async function getExtractor(modelName: string): Promise<any> {
  if (!extractors.has(modelName)) {
    const p = pipeline('feature-extraction', modelName);
    extractors.set(modelName, p);
  }
  return extractors.get(modelName)!;
}

export async function vectorize(
  text: string,
  modelName = 'Xenova/all-MiniLM-L6-v2'
): Promise<number[]> {
  const extractor = await getExtractor(modelName);

  const tensor = await extractor(text, {
    pooling: 'mean',
    normalize: true,
  });

  return Array.from(tensor.data as Float32Array);
}
