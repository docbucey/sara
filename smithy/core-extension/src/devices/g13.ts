// G13 device handler stub
export function handleG13Input(event: any) {
  // Normalize and process G13 input event
}

import { DeviceListener } from "./deviceListener";

export function simulateG13Input(control: string, value: any = 1) {
    DeviceListener.handleRawInput({
        device: "G13",
        control,
        value
    });
}
// G13 device handler stub
export function handleG13Input(event: any) {
  // Normalize and process G13 input event
}
