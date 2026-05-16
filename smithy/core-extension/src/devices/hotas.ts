// HOTAS device handler stub
export function handleHOTASInput(event: any) {
  // Normalize and process HOTAS input event
}

import { DeviceListener } from "./deviceListener";

export function simulateHOTASInput(control: string, value: any = 1) {
    DeviceListener.handleRawInput({
        device: "HOTAS",
        control,
        value
    });
}
// HOTAS device handler stub
export function handleHOTASInput(event: any) {
  // Normalize and process HOTAS input event
}
