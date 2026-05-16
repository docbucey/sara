// Voice device handler stub
import { DeviceListener } from "./deviceListener";

export function simulateVoiceInput(phrase: string) {
  DeviceListener.handleRawInput({
    device: "Voice",
    control: "Phrase",
    value: phrase
  });
}
export function handleVoiceInput(event: any) {
  // Normalize and process voice input event
}
