add_library(libvpx OBJECT)
init_target(libvpx)
add_library(tg_owt::libvpx ALIAS libvpx)

set(libvpx_loc ${third_party_loc}/libvpx)

set(include_directories
    ${libvpx_loc}/source/libvpx
    ${libvpx_loc}/source/config
)

if (WIN32)
    if (is_x86)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/win/ia32
        )
    elseif (is_x64)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/win/x64
        )
    elseif (is_aarch64)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/win/arm64
        )
    else()
        message(FATAL_ERROR "Unsupported CPU architecture on Windows.")
    endif()
    set(ASM_SUFFIX ".asm")
elseif (APPLE)
    if (is_x86)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/mac/ia32
        )
    elseif (is_x64)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/mac/x64
        )
    elseif (is_aarch64)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/linux/arm64
        )
    else()
        message(FATAL_ERROR "Unsupported CPU architecture on Apple devices.")
    endif()
else()
    if (is_x86)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/linux/ia32
        )
    elseif (is_x64)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/linux/x64
        )
    elseif (is_aarch64)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/linux/arm64
        )
    elseif (is_arm AND arm_use_neon)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/linux/arm-neon
        )
    elseif (is_arm)
        list(APPEND include_directories
            ${libvpx_loc}/source/config/linux/arm
        )
    else()
        list(APPEND include_directories
            ${libvpx_loc}/source/config/linux/generic
        )
    endif()

    set(ASM_SUFFIX ".asm.S")
endif()

foreach(dir ${include_directories})
    string(REPLACE ${libvpx_loc} ${webrtc_includedir}/third_party/libvpx install_include_dir ${dir})
    list(APPEND install_include_directories ${install_include_dir})
endforeach()

function(add_sublibrary postfix)
    add_library(libvpx_${postfix} OBJECT)
    init_feature_target(libvpx_${postfix} ${postfix})
    add_library(tg_owt::libvpx_${postfix} ALIAS libvpx_${postfix})
    target_include_directories(libvpx_${postfix}
    PRIVATE
        ${include_directories}
        "$<BUILD_INTERFACE:${include_directories}>"
        "$<INSTALL_INTERFACE:${install_include_directories}>"
    )
    set(sources_list ${ARGV})
    list(REMOVE_AT sources_list 0)
    nice_target_sources(libvpx_${postfix} ${libvpx_loc}
    PRIVATE
        ${sources_list}
    )
endfunction()

nice_target_sources(libvpx ${libvpx_loc}
PRIVATE
    include/elf.h

    # Source Files
    source/libvpx/vp8/common/alloccommon.c
    source/libvpx/vp8/common/alloccommon.h
    source/libvpx/vp8/common/blockd.c
    source/libvpx/vp8/common/blockd.h
    source/libvpx/vp8/common/coefupdateprobs.h
    source/libvpx/vp8/common/common.h
    source/libvpx/vp8/common/default_coef_probs.h
    source/libvpx/vp8/common/dequantize.c
    source/libvpx/vp8/common/entropy.c
    source/libvpx/vp8/common/entropy.h
    source/libvpx/vp8/common/entropymode.c
    source/libvpx/vp8/common/entropymode.h
    source/libvpx/vp8/common/entropymv.c
    source/libvpx/vp8/common/entropymv.h
    source/libvpx/vp8/common/extend.c
    source/libvpx/vp8/common/extend.h
    source/libvpx/vp8/common/filter.c
    source/libvpx/vp8/common/filter.h
    source/libvpx/vp8/common/findnearmv.c
    source/libvpx/vp8/common/findnearmv.h
    source/libvpx/vp8/common/generic/systemdependent.c
    source/libvpx/vp8/common/header.h
    source/libvpx/vp8/common/idct_blk.c
    source/libvpx/vp8/common/idctllm.c
    source/libvpx/vp8/common/invtrans.h
    source/libvpx/vp8/common/loopfilter.h
    source/libvpx/vp8/common/loopfilter_filters.c
    source/libvpx/vp8/common/mbpitch.c
    source/libvpx/vp8/common/mfqe.c
    source/libvpx/vp8/common/modecont.c
    source/libvpx/vp8/common/modecont.h
    source/libvpx/vp8/common/mv.h
    source/libvpx/vp8/common/onyx.h
    source/libvpx/vp8/common/onyxc_int.h
    source/libvpx/vp8/common/onyxd.h
    source/libvpx/vp8/common/postproc.c
    source/libvpx/vp8/common/postproc.h
    source/libvpx/vp8/common/ppflags.h
    source/libvpx/vp8/common/quant_common.c
    source/libvpx/vp8/common/quant_common.h
    source/libvpx/vp8/common/reconinter.c
    source/libvpx/vp8/common/reconinter.h
    source/libvpx/vp8/common/reconintra.c
    source/libvpx/vp8/common/reconintra.h
    source/libvpx/vp8/common/reconintra4x4.c
    source/libvpx/vp8/common/reconintra4x4.h
    source/libvpx/vp8/common/rtcd.c
    source/libvpx/vp8/common/setupintrarecon.c
    source/libvpx/vp8/common/setupintrarecon.h
    source/libvpx/vp8/common/swapyv12buffer.c
    source/libvpx/vp8/common/swapyv12buffer.h
    source/libvpx/vp8/common/systemdependent.h
    source/libvpx/vp8/common/threading.h
    source/libvpx/vp8/common/treecoder.c
    source/libvpx/vp8/common/treecoder.h
    source/libvpx/vp8/common/vp8_entropymodedata.h
    source/libvpx/vp8/common/vp8_loopfilter.c
    source/libvpx/vp8/common/vp8_skin_detection.c
    source/libvpx/vp8/common/vp8_skin_detection.h
    source/libvpx/vp8/decoder/dboolhuff.c
    source/libvpx/vp8/decoder/dboolhuff.h
    source/libvpx/vp8/decoder/decodeframe.c
    source/libvpx/vp8/decoder/decodemv.c
    source/libvpx/vp8/decoder/decodemv.h
    source/libvpx/vp8/decoder/decoderthreading.h
    source/libvpx/vp8/decoder/detokenize.c
    source/libvpx/vp8/decoder/detokenize.h
    source/libvpx/vp8/decoder/onyxd_if.c
    source/libvpx/vp8/decoder/onyxd_int.h
    source/libvpx/vp8/decoder/threading.c
    source/libvpx/vp8/decoder/treereader.h
    source/libvpx/vp8/encoder/bitstream.c
    source/libvpx/vp8/encoder/bitstream.h
    source/libvpx/vp8/encoder/block.h
    source/libvpx/vp8/encoder/boolhuff.c
    source/libvpx/vp8/encoder/boolhuff.h
    source/libvpx/vp8/encoder/copy_c.c
    source/libvpx/vp8/encoder/dct.c
    source/libvpx/vp8/encoder/dct_value_cost.h
    source/libvpx/vp8/encoder/dct_value_tokens.h
    source/libvpx/vp8/encoder/defaultcoefcounts.h
    source/libvpx/vp8/encoder/denoising.c
    source/libvpx/vp8/encoder/denoising.h
    source/libvpx/vp8/encoder/encodeframe.c
    source/libvpx/vp8/encoder/encodeframe.h
    source/libvpx/vp8/encoder/encodeintra.c
    source/libvpx/vp8/encoder/encodeintra.h
    source/libvpx/vp8/encoder/encodemb.c
    source/libvpx/vp8/encoder/encodemb.h
    source/libvpx/vp8/encoder/encodemv.c
    source/libvpx/vp8/encoder/encodemv.h
    source/libvpx/vp8/encoder/ethreading.c
    source/libvpx/vp8/encoder/ethreading.h
    source/libvpx/vp8/encoder/firstpass.h
    source/libvpx/vp8/encoder/lookahead.c
    source/libvpx/vp8/encoder/lookahead.h
    source/libvpx/vp8/encoder/mcomp.c
    source/libvpx/vp8/encoder/mcomp.h
    source/libvpx/vp8/encoder/modecosts.c
    source/libvpx/vp8/encoder/modecosts.h
    source/libvpx/vp8/encoder/mr_dissim.c
    source/libvpx/vp8/encoder/mr_dissim.h
    source/libvpx/vp8/encoder/onyx_if.c
    source/libvpx/vp8/encoder/onyx_int.h
    source/libvpx/vp8/encoder/pickinter.c
    source/libvpx/vp8/encoder/pickinter.h
    source/libvpx/vp8/encoder/picklpf.c
    source/libvpx/vp8/encoder/picklpf.h
    source/libvpx/vp8/encoder/quantize.h
    source/libvpx/vp8/encoder/ratectrl.c
    source/libvpx/vp8/encoder/ratectrl.h
    source/libvpx/vp8/encoder/rdopt.c
    source/libvpx/vp8/encoder/rdopt.h
    source/libvpx/vp8/encoder/segmentation.c
    source/libvpx/vp8/encoder/segmentation.h
    source/libvpx/vp8/encoder/tokenize.c
    source/libvpx/vp8/encoder/tokenize.h
    source/libvpx/vp8/encoder/treewriter.c
    source/libvpx/vp8/encoder/treewriter.h
    source/libvpx/vp8/encoder/vp8_quantize.c
    source/libvpx/vp8/vp8_cx_iface.c
    source/libvpx/vp8/vp8_dx_iface.c
    source/libvpx/vp9/common/vp9_alloccommon.c
    source/libvpx/vp9/common/vp9_alloccommon.h
    source/libvpx/vp9/common/vp9_blockd.c
    source/libvpx/vp9/common/vp9_blockd.h
    source/libvpx/vp9/common/vp9_common.h
    source/libvpx/vp9/common/vp9_common_data.c
    source/libvpx/vp9/common/vp9_common_data.h
    source/libvpx/vp9/common/vp9_entropy.c
    source/libvpx/vp9/common/vp9_entropy.h
    source/libvpx/vp9/common/vp9_entropymode.c
    source/libvpx/vp9/common/vp9_entropymode.h
    source/libvpx/vp9/common/vp9_entropymv.c
    source/libvpx/vp9/common/vp9_entropymv.h
    source/libvpx/vp9/common/vp9_enums.h
    source/libvpx/vp9/common/vp9_filter.c
    source/libvpx/vp9/common/vp9_filter.h
    source/libvpx/vp9/common/vp9_frame_buffers.c
    source/libvpx/vp9/common/vp9_frame_buffers.h
    source/libvpx/vp9/common/vp9_idct.c
    source/libvpx/vp9/common/vp9_idct.h
    source/libvpx/vp9/common/vp9_loopfilter.c
    source/libvpx/vp9/common/vp9_loopfilter.h
    source/libvpx/vp9/common/vp9_mfqe.c
    source/libvpx/vp9/common/vp9_mfqe.h
    source/libvpx/vp9/common/vp9_mv.h
    source/libvpx/vp9/common/vp9_mvref_common.c
    source/libvpx/vp9/common/vp9_mvref_common.h
    source/libvpx/vp9/common/vp9_onyxc_int.h
    source/libvpx/vp9/common/vp9_postproc.c
    source/libvpx/vp9/common/vp9_postproc.h
    source/libvpx/vp9/common/vp9_ppflags.h
    source/libvpx/vp9/common/vp9_pred_common.c
    source/libvpx/vp9/common/vp9_pred_common.h
    source/libvpx/vp9/common/vp9_quant_common.c
    source/libvpx/vp9/common/vp9_quant_common.h
    source/libvpx/vp9/common/vp9_reconinter.c
    source/libvpx/vp9/common/vp9_reconinter.h
    source/libvpx/vp9/common/vp9_reconintra.c
    source/libvpx/vp9/common/vp9_reconintra.h
    source/libvpx/vp9/common/vp9_rtcd.c
    source/libvpx/vp9/common/vp9_scale.c
    source/libvpx/vp9/common/vp9_scale.h
    source/libvpx/vp9/common/vp9_scan.c
    source/libvpx/vp9/common/vp9_scan.h
    source/libvpx/vp9/common/vp9_seg_common.c
    source/libvpx/vp9/common/vp9_seg_common.h
    source/libvpx/vp9/common/vp9_thread_common.c
    source/libvpx/vp9/common/vp9_thread_common.h
    source/libvpx/vp9/common/vp9_tile_common.c
    source/libvpx/vp9/common/vp9_tile_common.h
    source/libvpx/vp9/decoder/vp9_decodeframe.c
    source/libvpx/vp9/decoder/vp9_decodeframe.h
    source/libvpx/vp9/decoder/vp9_decodemv.c
    source/libvpx/vp9/decoder/vp9_decodemv.h
    source/libvpx/vp9/decoder/vp9_decoder.c
    source/libvpx/vp9/decoder/vp9_decoder.h
    source/libvpx/vp9/decoder/vp9_detokenize.c
    source/libvpx/vp9/decoder/vp9_detokenize.h
    source/libvpx/vp9/decoder/vp9_dsubexp.c
    source/libvpx/vp9/decoder/vp9_dsubexp.h
    source/libvpx/vp9/decoder/vp9_job_queue.c
    source/libvpx/vp9/decoder/vp9_job_queue.h
    source/libvpx/vp9/encoder/vp9_aq_cyclicrefresh.c
    source/libvpx/vp9/encoder/vp9_aq_cyclicrefresh.h
    source/libvpx/vp9/encoder/vp9_bitstream.c
    source/libvpx/vp9/encoder/vp9_bitstream.h
    source/libvpx/vp9/encoder/vp9_block.h
    source/libvpx/vp9/encoder/vp9_context_tree.c
    source/libvpx/vp9/encoder/vp9_context_tree.h
    source/libvpx/vp9/encoder/vp9_cost.c
    source/libvpx/vp9/encoder/vp9_cost.h
    source/libvpx/vp9/encoder/vp9_dct.c
    source/libvpx/vp9/encoder/vp9_denoiser.c
    source/libvpx/vp9/encoder/vp9_denoiser.h
    source/libvpx/vp9/encoder/vp9_encodeframe.c
    source/libvpx/vp9/encoder/vp9_encodeframe.h
    source/libvpx/vp9/encoder/vp9_encodemb.c
    source/libvpx/vp9/encoder/vp9_encodemb.h
    source/libvpx/vp9/encoder/vp9_encodemv.c
    source/libvpx/vp9/encoder/vp9_encodemv.h
    source/libvpx/vp9/encoder/vp9_encoder.c
    source/libvpx/vp9/encoder/vp9_encoder.h
    source/libvpx/vp9/encoder/vp9_ethread.c
    source/libvpx/vp9/encoder/vp9_ethread.h
    source/libvpx/vp9/encoder/vp9_ext_ratectrl.c
    source/libvpx/vp9/encoder/vp9_ext_ratectrl.h
    source/libvpx/vp9/encoder/vp9_extend.c
    source/libvpx/vp9/encoder/vp9_extend.h
    source/libvpx/vp9/encoder/vp9_firstpass.h
    source/libvpx/vp9/encoder/vp9_frame_scale.c
    source/libvpx/vp9/encoder/vp9_job_queue.h
    source/libvpx/vp9/encoder/vp9_lookahead.c
    source/libvpx/vp9/encoder/vp9_lookahead.h
    source/libvpx/vp9/encoder/vp9_mbgraph.h
    source/libvpx/vp9/encoder/vp9_mcomp.c
    source/libvpx/vp9/encoder/vp9_mcomp.h
    source/libvpx/vp9/encoder/vp9_multi_thread.c
    source/libvpx/vp9/encoder/vp9_multi_thread.h
    source/libvpx/vp9/encoder/vp9_noise_estimate.c
    source/libvpx/vp9/encoder/vp9_noise_estimate.h
    source/libvpx/vp9/encoder/vp9_partition_models.h
    source/libvpx/vp9/encoder/vp9_picklpf.c
    source/libvpx/vp9/encoder/vp9_picklpf.h
    source/libvpx/vp9/encoder/vp9_pickmode.c
    source/libvpx/vp9/encoder/vp9_pickmode.h
    source/libvpx/vp9/encoder/vp9_quantize.c
    source/libvpx/vp9/encoder/vp9_quantize.h
    source/libvpx/vp9/encoder/vp9_ratectrl.c
    source/libvpx/vp9/encoder/vp9_ratectrl.h
    source/libvpx/vp9/encoder/vp9_rd.c
    source/libvpx/vp9/encoder/vp9_rd.h
    source/libvpx/vp9/encoder/vp9_rdopt.c
    source/libvpx/vp9/encoder/vp9_rdopt.h
    source/libvpx/vp9/encoder/vp9_resize.c
    source/libvpx/vp9/encoder/vp9_resize.h
    source/libvpx/vp9/encoder/vp9_segmentation.c
    source/libvpx/vp9/encoder/vp9_segmentation.h
    source/libvpx/vp9/encoder/vp9_skin_detection.c
    source/libvpx/vp9/encoder/vp9_skin_detection.h
    source/libvpx/vp9/encoder/vp9_speed_features.c
    source/libvpx/vp9/encoder/vp9_speed_features.h
    source/libvpx/vp9/encoder/vp9_subexp.c
    source/libvpx/vp9/encoder/vp9_subexp.h
    source/libvpx/vp9/encoder/vp9_svc_layercontext.c
    source/libvpx/vp9/encoder/vp9_svc_layercontext.h
    source/libvpx/vp9/encoder/vp9_temporal_filter.h
    source/libvpx/vp9/encoder/vp9_tokenize.c
    source/libvpx/vp9/encoder/vp9_tokenize.h
    source/libvpx/vp9/encoder/vp9_treewriter.c
    source/libvpx/vp9/encoder/vp9_treewriter.h
    source/libvpx/vp9/vp9_cx_iface.c
    source/libvpx/vp9/vp9_cx_iface.h
    source/libvpx/vp9/vp9_dx_iface.c
    source/libvpx/vp9/vp9_dx_iface.h
    source/libvpx/vp9/vp9_iface_common.c
    source/libvpx/vp9/vp9_iface_common.h
    source/libvpx/vpx/internal/vpx_codec_internal.h
    source/libvpx/vpx/src/vpx_codec.c
    source/libvpx/vpx/src/vpx_decoder.c
    source/libvpx/vpx/src/vpx_encoder.c
    source/libvpx/vpx/src/vpx_image.c
    source/libvpx/vpx/vp8.h
    source/libvpx/vpx/vp8cx.h
    source/libvpx/vpx/vp8dx.h
    source/libvpx/vpx/vpx_codec.h
    source/libvpx/vpx/vpx_decoder.h
    source/libvpx/vpx/vpx_encoder.h
    source/libvpx/vpx/vpx_frame_buffer.h
    source/libvpx/vpx/vpx_image.h
    source/libvpx/vpx/vpx_integer.h
    source/libvpx/vpx_dsp/add_noise.c
    source/libvpx/vpx_dsp/avg.c
    source/libvpx/vpx_dsp/bitreader.c
    source/libvpx/vpx_dsp/bitreader.h
    source/libvpx/vpx_dsp/bitreader_buffer.c
    source/libvpx/vpx_dsp/bitreader_buffer.h
    source/libvpx/vpx_dsp/bitwriter.c
    source/libvpx/vpx_dsp/bitwriter.h
    source/libvpx/vpx_dsp/bitwriter_buffer.c
    source/libvpx/vpx_dsp/bitwriter_buffer.h
    source/libvpx/vpx_dsp/deblock.c
    source/libvpx/vpx_dsp/fwd_txfm.c
    source/libvpx/vpx_dsp/fwd_txfm.h
    source/libvpx/vpx_dsp/intrapred.c
    source/libvpx/vpx_dsp/inv_txfm.c
    source/libvpx/vpx_dsp/inv_txfm.h
    source/libvpx/vpx_dsp/loopfilter.c
    source/libvpx/vpx_dsp/postproc.h
    source/libvpx/vpx_dsp/prob.c
    source/libvpx/vpx_dsp/prob.h
    source/libvpx/vpx_dsp/psnr.c
    source/libvpx/vpx_dsp/psnr.h
    source/libvpx/vpx_dsp/quantize.c
    source/libvpx/vpx_dsp/quantize.h
    source/libvpx/vpx_dsp/sad.c
    source/libvpx/vpx_dsp/skin_detection.c
    source/libvpx/vpx_dsp/skin_detection.h
    source/libvpx/vpx_dsp/subtract.c
    source/libvpx/vpx_dsp/sum_squares.c
    source/libvpx/vpx_dsp/txfm_common.h
    source/libvpx/vpx_dsp/variance.c
    source/libvpx/vpx_dsp/variance.h
    source/libvpx/vpx_dsp/vpx_convolve.c
    source/libvpx/vpx_dsp/vpx_convolve.h
    source/libvpx/vpx_dsp/vpx_dsp_common.h
    source/libvpx/vpx_dsp/vpx_dsp_rtcd.c
    source/libvpx/vpx_dsp/vpx_filter.h
    source/libvpx/vpx_mem/include/vpx_mem_intrnl.h
    source/libvpx/vpx_mem/vpx_mem.c
    source/libvpx/vpx_mem/vpx_mem.h
    source/libvpx/vpx_ports/bitops.h
    source/libvpx/vpx_ports/compiler_attributes.h
    source/libvpx/vpx_ports/mem.h
    source/libvpx/vpx_ports/mem_ops.h
    source/libvpx/vpx_ports/mem_ops_aligned.h
    source/libvpx/vpx_ports/msvc.h
    source/libvpx/vpx_ports/static_assert.h
    source/libvpx/vpx_ports/system_state.h
    source/libvpx/vpx_ports/vpx_once.h
    source/libvpx/vpx_ports/vpx_timer.h
    source/libvpx/vpx_scale/generic/gen_scalers.c
    source/libvpx/vpx_scale/generic/vpx_scale.c
    source/libvpx/vpx_scale/generic/yv12config.c
    source/libvpx/vpx_scale/generic/yv12extend.c
    source/libvpx/vpx_scale/vpx_scale.h
    source/libvpx/vpx_scale/vpx_scale_rtcd.c
    source/libvpx/vpx_scale/yv12config.h
    source/libvpx/vpx_util/endian_inl.h
    source/libvpx/vpx_util/vpx_atomics.h
    source/libvpx/vpx_util/vpx_thread.c
    source/libvpx/vpx_util/vpx_thread.h
    source/libvpx/vpx_util/vpx_timestamp.h
    source/libvpx/vpx_util/vpx_write_yuv_frame.c
    source/libvpx/vpx_util/vpx_write_yuv_frame.h
)

if (is_x86 OR is_x64)
    nice_target_sources(libvpx ${libvpx_loc}
    PRIVATE

        source/libvpx/vp8/common/x86/loopfilter_x86.c
        source/libvpx/vp8/common/x86/vp8_asm_stubs.c
        source/libvpx/vpx_dsp/x86/bitdepth_conversion_avx2.h
        source/libvpx/vpx_dsp/x86/bitdepth_conversion_sse2.h
        source/libvpx/vpx_dsp/x86/convolve.h
        source/libvpx/vpx_dsp/x86/convolve_avx2.h
        source/libvpx/vpx_dsp/x86/convolve_sse2.h
        source/libvpx/vpx_dsp/x86/convolve_ssse3.h
        source/libvpx/vpx_dsp/x86/fwd_dct32x32_impl_avx2.h
        source/libvpx/vpx_dsp/x86/fwd_dct32x32_impl_sse2.h
        source/libvpx/vpx_dsp/x86/fwd_txfm_impl_sse2.h
        source/libvpx/vpx_dsp/x86/fwd_txfm_sse2.h
        source/libvpx/vpx_dsp/x86/highbd_inv_txfm_sse2.h
        source/libvpx/vpx_dsp/x86/highbd_inv_txfm_sse4.h
        source/libvpx/vpx_dsp/x86/inv_txfm_sse2.h
        source/libvpx/vpx_dsp/x86/inv_txfm_ssse3.h
        source/libvpx/vpx_dsp/x86/mem_sse2.h
        source/libvpx/vpx_dsp/x86/quantize_sse2.h
        source/libvpx/vpx_dsp/x86/quantize_ssse3.h
        source/libvpx/vpx_dsp/x86/transpose_sse2.h
        source/libvpx/vpx_dsp/x86/txfm_common_sse2.h
        source/libvpx/vpx_ports/emmintrin_compat.h
        source/libvpx/vpx_ports/x86.h
    )

    add_sublibrary(mmx
        source/libvpx/vp8/common/x86/idct_blk_mmx.c
        source/libvpx/vpx_ports/emms_mmx.c
    )

    add_sublibrary(sse2
        source/libvpx/vp8/common/x86/bilinear_filter_sse2.c
        source/libvpx/vp8/common/x86/idct_blk_sse2.c
        source/libvpx/vp8/encoder/x86/denoising_sse2.c
        source/libvpx/vp8/encoder/x86/vp8_enc_stubs_sse2.c
        source/libvpx/vp8/encoder/x86/vp8_quantize_sse2.c
        source/libvpx/vp9/common/x86/vp9_idct_intrin_sse2.c
        source/libvpx/vp9/encoder/x86/vp9_dct_intrin_sse2.c
        source/libvpx/vp9/encoder/x86/vp9_denoiser_sse2.c
        source/libvpx/vp9/encoder/x86/vp9_highbd_block_error_intrin_sse2.c
        source/libvpx/vp9/encoder/x86/vp9_quantize_sse2.c
        source/libvpx/vpx_dsp/x86/avg_intrin_sse2.c
        source/libvpx/vpx_dsp/x86/avg_pred_sse2.c
        source/libvpx/vpx_dsp/x86/fwd_txfm_sse2.c
        source/libvpx/vpx_dsp/x86/highbd_idct16x16_add_sse2.c
        source/libvpx/vpx_dsp/x86/highbd_idct32x32_add_sse2.c
        source/libvpx/vpx_dsp/x86/highbd_idct4x4_add_sse2.c
        source/libvpx/vpx_dsp/x86/highbd_idct8x8_add_sse2.c
        source/libvpx/vpx_dsp/x86/highbd_intrapred_intrin_sse2.c
        source/libvpx/vpx_dsp/x86/highbd_loopfilter_sse2.c
        source/libvpx/vpx_dsp/x86/highbd_quantize_intrin_sse2.c
        source/libvpx/vpx_dsp/x86/highbd_variance_sse2.c
        source/libvpx/vpx_dsp/x86/inv_txfm_sse2.c
        source/libvpx/vpx_dsp/x86/loopfilter_sse2.c
        source/libvpx/vpx_dsp/x86/post_proc_sse2.c
        source/libvpx/vpx_dsp/x86/quantize_sse2.c
        source/libvpx/vpx_dsp/x86/sum_squares_sse2.c
        source/libvpx/vpx_dsp/x86/variance_sse2.c
        source/libvpx/vpx_dsp/x86/vpx_subpixel_4t_intrin_sse2.c
    )

    add_sublibrary(ssse3
        source/libvpx/vp8/encoder/x86/vp8_quantize_ssse3.c
        source/libvpx/vp9/encoder/x86/vp9_frame_scale_ssse3.c
        source/libvpx/vpx_dsp/x86/highbd_intrapred_intrin_ssse3.c
        source/libvpx/vpx_dsp/x86/inv_txfm_ssse3.c
        source/libvpx/vpx_dsp/x86/quantize_ssse3.c
        source/libvpx/vpx_dsp/x86/vpx_subpixel_8t_intrin_ssse3.c
    )

    add_sublibrary(sse4
        source/libvpx/vp8/encoder/x86/quantize_sse4.c
        source/libvpx/vp9/common/x86/vp9_highbd_iht16x16_add_sse4.c
        source/libvpx/vp9/common/x86/vp9_highbd_iht4x4_add_sse4.c
        source/libvpx/vp9/common/x86/vp9_highbd_iht8x8_add_sse4.c
        source/libvpx/vpx_dsp/x86/highbd_idct16x16_add_sse4.c
        source/libvpx/vpx_dsp/x86/highbd_idct32x32_add_sse4.c
        source/libvpx/vpx_dsp/x86/highbd_idct4x4_add_sse4.c
        source/libvpx/vpx_dsp/x86/highbd_idct8x8_add_sse4.c
    )

    add_sublibrary(avx
        source/libvpx/vp9/encoder/x86/vp9_diamond_search_sad_avx.c
        source/libvpx/vpx_dsp/x86/quantize_avx.c
    )

    add_sublibrary(avx2
        source/libvpx/vp9/encoder/x86/vp9_error_avx2.c
        source/libvpx/vp9/encoder/x86/vp9_quantize_avx2.c
        source/libvpx/vpx_dsp/x86/avg_intrin_avx2.c
        source/libvpx/vpx_dsp/x86/fwd_txfm_avx2.c
        source/libvpx/vpx_dsp/x86/highbd_convolve_avx2.c
        source/libvpx/vpx_dsp/x86/loopfilter_avx2.c
        source/libvpx/vpx_dsp/x86/sad4d_avx2.c
        source/libvpx/vpx_dsp/x86/sad_avx2.c
        source/libvpx/vpx_dsp/x86/variance_avx2.c
        source/libvpx/vpx_dsp/x86/vpx_subpixel_8t_intrin_avx2.c
    )

    set(yasm_sources
        source/libvpx/vp8/common/x86/dequantize_mmx.asm
        source/libvpx/vp8/common/x86/idctllm_mmx.asm
        source/libvpx/vp8/common/x86/idctllm_sse2.asm
        source/libvpx/vp8/common/x86/iwalsh_sse2.asm
        source/libvpx/vp8/common/x86/loopfilter_sse2.asm
        source/libvpx/vp8/common/x86/mfqe_sse2.asm
        source/libvpx/vp8/common/x86/recon_mmx.asm
        source/libvpx/vp8/common/x86/recon_sse2.asm
        source/libvpx/vp8/common/x86/subpixel_mmx.asm
        source/libvpx/vp8/common/x86/subpixel_sse2.asm
        source/libvpx/vp8/common/x86/subpixel_ssse3.asm
        source/libvpx/vp8/encoder/x86/block_error_sse2.asm
        source/libvpx/vp8/encoder/x86/copy_sse2.asm
        source/libvpx/vp8/encoder/x86/copy_sse3.asm
        source/libvpx/vp8/encoder/x86/dct_sse2.asm
        source/libvpx/vp8/encoder/x86/fwalsh_sse2.asm
        source/libvpx/vp9/common/x86/vp9_mfqe_sse2.asm
        source/libvpx/vp9/encoder/x86/vp9_dct_sse2.asm
        source/libvpx/vp9/encoder/x86/vp9_error_sse2.asm
        source/libvpx/vpx_dsp/x86/add_noise_sse2.asm
        source/libvpx/vpx_dsp/x86/deblock_sse2.asm
        source/libvpx/vpx_dsp/x86/highbd_intrapred_sse2.asm
        source/libvpx/vpx_dsp/x86/highbd_sad4d_sse2.asm
        source/libvpx/vpx_dsp/x86/highbd_sad_sse2.asm
        source/libvpx/vpx_dsp/x86/highbd_subpel_variance_impl_sse2.asm
        source/libvpx/vpx_dsp/x86/highbd_variance_impl_sse2.asm
        source/libvpx/vpx_dsp/x86/intrapred_sse2.asm
        source/libvpx/vpx_dsp/x86/intrapred_ssse3.asm
        source/libvpx/vpx_dsp/x86/inv_wht_sse2.asm
        source/libvpx/vpx_dsp/x86/sad4d_sse2.asm
        source/libvpx/vpx_dsp/x86/sad_sse2.asm
        source/libvpx/vpx_dsp/x86/sad_sse3.asm
        source/libvpx/vpx_dsp/x86/sad_sse4.asm
        source/libvpx/vpx_dsp/x86/sad_ssse3.asm
        source/libvpx/vpx_dsp/x86/subpel_variance_sse2.asm
        source/libvpx/vpx_dsp/x86/subtract_sse2.asm
        source/libvpx/vpx_dsp/x86/vpx_convolve_copy_sse2.asm
        source/libvpx/vpx_dsp/x86/vpx_high_subpixel_8t_sse2.asm
        source/libvpx/vpx_dsp/x86/vpx_high_subpixel_bilinear_sse2.asm
        source/libvpx/vpx_dsp/x86/vpx_subpixel_8t_sse2.asm
        source/libvpx/vpx_dsp/x86/vpx_subpixel_8t_ssse3.asm
        source/libvpx/vpx_dsp/x86/vpx_subpixel_bilinear_sse2.asm
        source/libvpx/vpx_dsp/x86/vpx_subpixel_bilinear_ssse3.asm
    )

    if (APPLE)
        remove_target_sources(libvpx_avx2 ${libvpx_loc}
            source/libvpx/vpx_dsp/x86/fwd_txfm_avx2.c
        )
    endif()

    if (is_x64)
        remove_target_sources(libvpx_mmx ${libvpx_loc}
            source/libvpx/vpx_ports/emms_mmx.c
        )
        list(APPEND yasm_sources
            source/libvpx/vp8/common/x86/loopfilter_block_sse2_x86_64.asm
            source/libvpx/vp9/encoder/x86/vp9_quantize_ssse3_x86_64.asm
            source/libvpx/vpx_dsp/x86/avg_ssse3_x86_64.asm
            source/libvpx/vpx_dsp/x86/fwd_txfm_ssse3_x86_64.asm
            source/libvpx/vpx_dsp/x86/ssim_opt_x86_64.asm
            source/libvpx/vpx_ports/emms_mmx.asm
            source/libvpx/vpx_ports/float_control_word.asm
        )
    endif()

    target_yasm_sources(libvpx ${libvpx_loc}
    INCLUDE_DIRECTORIES
        ${include_directories}
    DEFINES
        CHROMIUM
    SOURCES
        ${yasm_sources}
    )

elseif (is_arm OR is_aarch64)

    # General ARM source files
    nice_target_sources(libvpx ${libvpx_loc}
    PRIVATE
        source/libvpx/vpx_ports/arm.h
        source/libvpx/vpx_ports/arm_cpudetect.c
    )

    # C with NEON intrinsics
    if (arm_use_neon)
        nice_target_sources(libvpx ${libvpx_loc}
        PRIVATE

            source/libvpx/vp8/common/arm/loopfilter_arm.c
            source/libvpx/vp8/common/arm/loopfilter_arm.h
            source/libvpx/vp8/common/arm/neon/bilinearpredict_neon.c
            source/libvpx/vp8/common/arm/neon/copymem_neon.c
            source/libvpx/vp8/common/arm/neon/dc_only_idct_add_neon.c
            source/libvpx/vp8/common/arm/neon/dequant_idct_neon.c
            source/libvpx/vp8/common/arm/neon/dequantizeb_neon.c
            source/libvpx/vp8/common/arm/neon/idct_blk_neon.c
            source/libvpx/vp8/common/arm/neon/iwalsh_neon.c
            source/libvpx/vp8/common/arm/neon/loopfiltersimplehorizontaledge_neon.c
            source/libvpx/vp8/common/arm/neon/loopfiltersimpleverticaledge_neon.c
            source/libvpx/vp8/common/arm/neon/mbloopfilter_neon.c
            source/libvpx/vp8/common/arm/neon/shortidct4x4llm_neon.c
            source/libvpx/vp8/common/arm/neon/sixtappredict_neon.c
            source/libvpx/vp8/common/arm/neon/vp8_loopfilter_neon.c
            source/libvpx/vp8/encoder/arm/neon/denoising_neon.c
            source/libvpx/vp8/encoder/arm/neon/fastquantizeb_neon.c
            source/libvpx/vp8/encoder/arm/neon/shortfdct_neon.c
            source/libvpx/vp8/encoder/arm/neon/vp8_shortwalsh4x4_neon.c
            source/libvpx/vp9/common/arm/neon/vp9_iht16x16_add_neon.c
            source/libvpx/vp9/common/arm/neon/vp9_iht4x4_add_neon.c
            source/libvpx/vp9/common/arm/neon/vp9_iht8x8_add_neon.c
            source/libvpx/vp9/common/arm/neon/vp9_iht_neon.h
            source/libvpx/vp9/encoder/arm/neon/vp9_denoiser_neon.c
            source/libvpx/vp9/encoder/arm/neon/vp9_error_neon.c
            source/libvpx/vp9/encoder/arm/neon/vp9_frame_scale_neon.c
            source/libvpx/vp9/encoder/arm/neon/vp9_quantize_neon.c
            source/libvpx/vpx_dsp/arm/deblock_neon.c
            source/libvpx/vpx_dsp/arm/intrapred_neon.c
            source/libvpx/vpx_dsp/arm/vpx_scaled_convolve8_neon.c
            source/libvpx/vpx_dsp/arm/fdct_neon.c
            source/libvpx/vpx_dsp/arm/fdct16x16_neon.c
            source/libvpx/vpx_dsp/arm/fdct32x32_neon.c
            source/libvpx/vpx_dsp/arm/fdct_partial_neon.c
            source/libvpx/vpx_dsp/arm/fwd_txfm_neon.c
            source/libvpx/vpx_dsp/arm/idct_neon.h
            source/libvpx/vpx_dsp/arm/idct8x8_1_add_neon.c
            source/libvpx/vpx_dsp/arm/idct8x8_add_neon.c
            source/libvpx/vpx_dsp/arm/idct16x16_1_add_neon.c
            source/libvpx/vpx_dsp/arm/idct16x16_add_neon.c
            source/libvpx/vpx_dsp/arm/idct32x32_1_add_neon.c
            source/libvpx/vpx_dsp/arm/idct32x32_34_add_neon.c
            source/libvpx/vpx_dsp/arm/idct32x32_135_add_neon.c
            source/libvpx/vpx_dsp/arm/idct32x32_add_neon.c
            source/libvpx/vpx_dsp/arm/quantize_neon.c
            source/libvpx/vpx_dsp/arm/avg_neon.c
            source/libvpx/vpx_dsp/arm/hadamard_neon.c
            source/libvpx/vpx_dsp/arm/sum_squares_neon.c
            source/libvpx/vpx_dsp/arm/sad4d_neon.c
            source/libvpx/vpx_dsp/arm/sad_neon.c
            source/libvpx/vpx_dsp/arm/subtract_neon.c
            source/libvpx/vpx_dsp/arm/avg_pred_neon.c
            source/libvpx/vpx_dsp/arm/subpel_variance_neon.c
            source/libvpx/vpx_dsp/arm/variance_neon.c
            source/libvpx/vpx_dsp/arm/mem_neon.h
            source/libvpx/vpx_dsp/arm/sum_neon.h
            source/libvpx/vpx_dsp/arm/transpose_neon.h
            source/libvpx/vpx_dsp/arm/vpx_convolve8_neon.h
        )
    endif()

    # 32-bit assembly with NEON instructions
    if (arm_use_neon AND (NOT is_aarch64))
        nice_target_sources(libvpx ${libvpx_loc}
        PRIVATE

            source/libvpx/vpx_dsp/arm/intrapred_neon_asm${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve_copy_neon_asm${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_horiz_filter_type2_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_vert_filter_type2_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_horiz_filter_type1_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_vert_filter_type1_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_avg_horiz_filter_type2_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_avg_vert_filter_type2_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_avg_horiz_filter_type1_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_avg_vert_filter_type1_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve_avg_neon_asm${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/vpx_convolve8_neon_asm.c
            source/libvpx/vpx_dsp/arm/vpx_convolve8_neon_asm.h
            source/libvpx/vpx_dsp/arm/vpx_convolve_neon.c
            source/libvpx/vpx_dsp/arm/loopfilter_16_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/loopfilter_8_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/loopfilter_4_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/save_reg_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/idct_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/idct4x4_1_add_neon${ASM_SUFFIX}
            source/libvpx/vpx_dsp/arm/idct4x4_add_neon${ASM_SUFFIX}
    )

    # C versions of the above hand-optimized files, when available
    elseif (arm_use_neon AND is_aarch64)
        nice_target_sources(libvpx ${libvpx_loc}
        PRIVATE

            source/libvpx/vpx_dsp/arm/vpx_convolve_copy_neon.c
            source/libvpx/vpx_dsp/arm/vpx_convolve8_neon.c
            source/libvpx/vpx_dsp/arm/vpx_convolve_avg_neon.c
            source/libvpx/vpx_dsp/arm/vpx_convolve_neon.c
            source/libvpx/vpx_dsp/arm/loopfilter_neon.c
            source/libvpx/vpx_dsp/arm/idct4x4_1_add_neon.c
            source/libvpx/vpx_dsp/arm/idct4x4_add_neon.c
    )
    endif()
endif()

target_include_directories(libvpx
PUBLIC
    "$<BUILD_INTERFACE:${include_directories}>"
    "$<INSTALL_INTERFACE:${install_include_directories}>"
)
