export interface DeviceEvent {
    device: string;      // "G13", "HOTAS", "Mouse", "Voice"
    control: string;     // "G1", "AxisX", "Button4", "Phrase"
    value: any;          // number | boolean | string
}
