// Mouse device handler stub
import { DeviceListener } from "./deviceListener";

export function simulateMouseInput(control: string, value: any = 1) {
  DeviceListener.handleRawInput({
    device: "Mouse",
    control,
    value
  });
}
// Mouse device handler stub
export function handleMouseInput(event: any) {
  // Normalize and process mouse input event
}
