"""SARA CORE — The Engine. Foundation layer for storage, memory, file I/O, and data structures."""

try:
    from .proto_lingua import _classify_value_suffix, _to_proto_lingua, validate_resonance
except ImportError:
    pass

try:
    from .amip import (
        core_validate_ami_id, core_default_ami_id, resolve_machine_profile_core,
        build_amip_payload_core, build_bucey_shunt_envelope_core,
        unwrap_bucey_shunt_core, build_core_lite_bundle_core,
    )
except ImportError:
    pass

try:
    from .nbs import (
        NBS_BASE_DIR, SYSTEM_CORE_PROJECT_NAME,
        create_nbs_reference, in_out_nbs_file, create_nbs_file,
        create_characterbase_nbs_profile, create_nbs_project_profile,
        update_nbs_project_profile, append_event,
    )
except ImportError:
    pass

try:
    from .shunt import core_shunt_entrypoint, build_vnce_shunt_envelope
except ImportError:
    pass

try:
    from .compression import (
        core_compress_bytes, core_decompress_bytes, core_detect_compression_format,
        core_checksum_bytes, core_extract_full, core_extract_target,
    )
except ImportError:
    pass

try:
    from .file_io import (
        read_image_file, write_image_file, resize_image_file,
        read_video_file, read_audio_file, read_3d_file, read_graphics_asset_file,
        read_word_docx, write_word_docx, read_excel_xlsx, write_excel_xlsx,
        read_powerpoint_pptx, write_powerpoint_pptx,
    )
except ImportError:
    pass

try:
    from .persistence import SaraMemoryIO, memory_set, memory_get, memory_delete, memory_usage_report
except ImportError:
    pass
