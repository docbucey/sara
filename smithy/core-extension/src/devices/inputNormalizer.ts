export interface NormalizedInput {
    device: string;
    control: string;
    value: number | boolean | string;
}

export function normalizeInput(raw: any): NormalizedInput {
    return {
        device: raw.device || "unknown",
        control: raw.control || "unknown",
        value: raw.value ?? 0
    };
}
