

# SARA LLC UI Library Priority List

This document outlines a prioritized list of `core_llc` hardware modules to focus on when building a custom User Interface library. The priorities are structured to build from fundamental components to more advanced features.

---

## Priority 1: Core UI Fundamentals

These are the absolute essential modules required to get a basic graphical user interface up and running. They handle display output, user input, and fundamental processing.

-   **Core Processing & OS:**
    -   `core_cpu.slm`: For general computation and drawing primitives.
        -   `draw.rect(x, y, width, height, color)`: Draws a filled rectangle to the framebuffer.
        -   `draw.line(x1, y1, x2, y2, color)`: Draws a line.
        -   `draw.text(x, y, string_ptr, font_ptr, color)`: Renders text.
    -   `core_os.slm`: To interface with the underlying operating system for windowing and event handling.
        -   `os.create_window(width, height, title_ptr)`: Returns a window handle.
        -   `os.destroy_window(handle)`: Closes a window.
        -   `os.poll_events()`: Processes the OS event queue.
    -   `core_data.slm`: For managing data structures used in the UI, primarily the framebuffer.
        -   `data.create_framebuffer(width, height)`: Returns a handle to a new framebuffer.
        -   `data.set_pixel(fb_handle, x, y, color)`: Sets a pixel in a framebuffer.
        -   `data.get_framebuffer_ptr(fb_handle)`: Gets the raw memory pointer for rendering.
    -   `core_time.slm`: For animations, timers, and event timestamps.
        -   `time.get_ticks()`: Returns monotonic time in milliseconds.
        -   `time.delay(ms)`: Pauses execution.

-   **Display & Graphics:**
    -   `peripherals_llc/sara_display_controller.slam`: The most critical module for rendering pixels to a screen.
        -   `display.init(window_handle)`: Initializes the rendering context.
        -   `display.render_frame(framebuffer_ptr)`: Copies the framebuffer to the screen.
    -   `terminal_llc/sara_display_adapter.slam`: Manages the connection to the physical display.
        -   `adapter.detect_modes()`: Returns a list of supported resolutions and refresh rates.
        -   `adapter.set_mode(width, height, refresh)`: Sets the display mode.
    -   `terminal_llc/sara_integrated_gpu.slam` / `terminal_llc/sara_discrete_gpu.slam`: For graphics acceleration.
        -   `gpu.accel_rect_fill(fb_handle, x, y, width, height, color)`: Offloads rectangle drawing to hardware.
        -   `gpu.accel_blit(src_fb, dest_fb, src_rect, dest_rect)`: Offloads framebuffer copying.

-   **Basic Input:**
    -   `peripherals_llc/sara_keyboard_controller.slam`: To handle keyboard input.
        -   `keyboard.get_last_press()`: Returns the most recent key event.
        -   `keyboard.is_key_down(keycode)`: Checks if a specific key is currently held down.
    -   `peripherals_llc/sara_mouse_controller.slam`: To handle mouse/pointer input.
        -   `mouse.get_position()`: Returns the current (x, y) coordinates.
        -   `mouse.get_button_state()`: Returns a bitmask of button states (left, right, middle).
    -   `peripherals_llc/sara_touchpad_controller.slam`: For laptop/integrated touchpad support.
        -   `touchpad.get_touch_state()`: Returns state for multi-touch gestures (e.g., pinch, swipe).
    -   `peripherals_llc/sara_usb_controller.slam`: Essential for most modern input devices.
        -   `usb.enumerate_devices()`: Lists connected USB devices.
        -   `usb.get_device_handle(vendor_id, product_id)`: Gets a handle to a specific device for direct communication.

---

## Priority 2: Standard UI Components

Once the fundamentals are in place, these modules support common UI features like audio feedback, advanced input, and basic window management.

-   **Audio:**
    -   `peripherals_llc/sara_audio_codec.slam`: For processing and playing sound.
        -   `audio.load_wav(file_path)`: Loads a .wav file into memory.
        -   `audio.play_sound(sound_handle, volume)`: Plays a loaded sound.
        -   `audio.init_mic()`: Initializes microphone for recording.
    -   `peripherals_llc/sara_speaker_amplifier.slam`: To drive speakers for UI sounds.
        -   `speaker.set_volume(level)`: Sets the master volume.
        -   `speaker.mute()`: Mutes all audio output.
    -   `peripherals_llc/sara_microphone_interface.slam`: For voice input and commands.
        -   `mic.start_recording(buffer_handle)`: Starts capturing audio to a buffer.
        -   `mic.stop_recording()`: Stops capturing audio.

-   **Display Enhancements:**
    -   `peripherals_llc/sara_backlight_controller.slam`: For controlling screen brightness.
        -   `backlight.set_brightness(level)`: Sets screen brightness (0-100).
        -   `backlight.get_brightness()`: Returns the current brightness level.

-   **System Integration:**
    -   `peripherals_llc/sara_interrupt_controller.slam`: For efficient handling of input events.
        -   `irq.register_handler(device_id, function_ptr)`: Registers a callback function for a hardware interrupt.
        -   `irq.enable_interrupt(irq_line)`: Enables a specific interrupt line.
        -   `wifi.scan_networks()`: Returns a list of available Wi-Fi networks.
        -   `wifi.connect(ssid, password)`: Connects to a network.
        -   `wifi.get_status()`: Returns the current connection status.
    -   `peripherals_llc/sara_ethernet_controller.slam`: For wired network connectivity.
        -   `eth.get_mac_address()`: Returns the hardware MAC address.
        -   `eth.get_link_status()`: Checks if a cable is connected.
    -   `peripherals_llc/sara_bluetooth_controller.slam`: For connecting to Bluetooth peripherals.
        -   `bt.scan_devices()`: Finds nearby Bluetooth devices.
        -   `bt.pair_device(mac_address)`: Initiates pairing with a device.

-   **Smart Device & IoT Integration:**
    -   `smartdevices_llc/sara_smart_display.slam`: For interfacing with dedicated smart display hardware.
        -   `smartdisplay.push_notification(title, message)`: Sends a notification to the display.
        -   `smartdisplay.set_ambient_mode(mode)`: Sets the display to a low-power ambient mode.
    -   `smartdevices_llc/sara_smart_speaker.slam`: For creating voice-first UIs.
        -   `smartspeaker.speak_text(text_ptr)`: Uses text-to-speech to speak a phrase.
        -   `smartspeaker.listen_for_command(command_list_ptr)`: Listens for a specific voice command.
    -   `smartdevices_llc/sara_smart_remote.slam`: For building remote control interfaces.
        -   `remote.map_button(button_id, function_ptr)`: Assigns a function to a physical button press.
        -   `remote.vibrate(duration_ms)`: Triggers haptic feedback.

-   **Specialized Input/Output:**
    -   `maker_llc/sara_rpi_40pin_header.slam`: For building UIs on Raspberry Pi platforms.
        -   `gpio.set_pin_mode(pin_number, mode)`: Sets a GPIO pin to input or output.
        -   `gpio.write_pin(pin_number, value)`: Sets a GPIO pin's value (high/low).
        -   `gpio.read_pin(pin_number)`: Reads a GPIO pin's value.
    -   `legacy_llc/sara_serial_rs232.slam`: For interfacing with older industrial or legacy hardware that may have a UI component.
        -   `serial.open_port(port_name, baud_rate)`: Opens a serial port.
        -   `serial.write_data(port_handle, data_ptr)`: Sends data over the serial connection.
        -   `serial.read_data(port_handle, buffer_ptr)`: Reads data from the serial connection
These modules are for more advanced or specialized UI applications, including networking, smart device integration, and custom hardware interactions.

-   **Connectivity:**
    -   `peripherals_llc/sara_wifi_controller.slam`: For wireless network connectivity.
    -   `peripherals_llc/sara_ethernet_controller.slam`: For wired network connectivity.
    -   `peripherals_llc/sara_bluetooth_controller.slam`: For connecting to Bluetooth peripherals.

-   **Smart Device & IoT Integration:**
    -   `smartdevices_llc/sara_smart_display.slam`: For interfacing with dedicated smart display hardware.
    -   `smartdevices_llc/sara_smart_speaker.slam`: For creating voice-first UIs.
    -   `smartdevices_llc/sara_smart_remote.slam`: For building remote control interfaces.

-   **Specialized Input/Output:**
    -   `maker_llc/sara_rpi_40pin_header.slam`: For building UIs on Raspberry Pi platforms.
    -   `legacy_llc/sara_serial_rs232.slam`: For interfacing with older industrial or legacy hardware that may have a UI component.
