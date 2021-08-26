include(cmake/external_ffmpeg.cmake)
include(cmake/lib_tgcalls.cmake)

configure_file("${src_loc}/config.h.in" "${src_loc}/config.h")

list(APPEND SOURCES
    ${src_loc}/config.h
    ${src_loc}/tgcalls.cpp
    ${src_loc}/WrappedAudioDeviceModuleImpl.h
    ${src_loc}/WrappedAudioDeviceModuleImpl.cpp
    ${src_loc}/FileAudioDevice.cpp
    ${src_loc}/FileAudioDevice.h
    ${src_loc}/RawAudioDevice.h
    ${src_loc}/RawAudioDevice.cpp
    ${src_loc}/FileAudioDeviceDescriptor.h
    ${src_loc}/RawAudioDeviceDescriptor.h
    ${src_loc}/RawAudioDeviceDescriptor.cpp
    ${src_loc}/NativeInstance.h
    ${src_loc}/NativeInstance.cpp
    ${src_loc}/RtcServer.h
    ${src_loc}/RtcServer.cpp
    ${src_loc}/InstanceHolder.h
)

pybind11_add_module(tgcalls ${SOURCES})

if (WIN32)
  target_compile_features(tgcalls
  PUBLIC
      cxx_std_20
  )
endif()

message(${OpenCV_LIBS})
target_link_libraries(tgcalls
PRIVATE
    lib_tgcalls
    external_ffmpeg
    external_webrtc
    opencv_calib3d opencv_core opencv_dnn opencv_features2d opencv_flann opencv_gapi opencv_highgui opencv_imgcodecs opencv_imgproc opencv_ml opencv_objdetect opencv_photo opencv_stitching opencv_video opencv_videoio opencv_alphamat opencv_aruco opencv_barcode opencv_bgsegm opencv_bioinspired opencv_ccalib opencv_datasets opencv_dnn_objdetect opencv_dnn_superres opencv_dpm opencv_face opencv_freetype opencv_fuzzy opencv_hfs opencv_img_hash opencv_intensity_transform opencv_line_descriptor opencv_mcc opencv_optflow opencv_phase_unwrapping opencv_plot opencv_quality opencv_rapid opencv_reg opencv_rgbd opencv_saliency opencv_sfm opencv_shape opencv_stereo opencv_structured_light opencv_superres opencv_surface_matching opencv_text opencv_tracking opencv_videostab opencv_viz opencv_wechat_qrcode opencv_xfeatures2d opencv_ximgproc opencv_xobjdetect opencv_xphoto
)
