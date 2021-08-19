/*
 *  Copyright (c) 2013 The WebRTC project authors. All Rights Reserved.
 *
 *  Use of this source code is governed by a BSD-style license
 *  that can be found in the LICENSE file in the root of the source
 *  tree. An additional intellectual property rights grant can be found
 *  in the file PATENTS.  All contributing project authors may
 *  be found in the AUTHORS file in the root of the source tree.
 */

#include "modules/desktop_capture/linux/x_error_trap.h"

#include <assert.h>
#include <stddef.h>
#include <atomic>

#if defined(TOOLKIT_GTK)
#include <gdk/gdk.h>
#endif  // !defined(TOOLKIT_GTK)

namespace webrtc {

namespace {

#if !defined(TOOLKIT_GTK)

std::atomic<int> g_xserver_error_trap_level/* = 0*/;
std::atomic<int> g_last_xserver_error_code/* = 0*/;
XErrorHandler g_original_error_handler_/* = nullptr*/;

int XServerErrorHandler(Display* display, XErrorEvent* error_event) {
  assert(g_xserver_error_trap_level > 0);
  g_last_xserver_error_code = error_event->error_code;
  return 0;
}

#endif  // !defined(TOOLKIT_GTK)

}  // namespace

XErrorTrap::XErrorTrap(Display* display)
    : original_error_handler_(NULL), enabled_(true) {
#if defined(TOOLKIT_GTK)
  gdk_error_trap_push();
#else   // !defined(TOOLKIT_GTK)
  if (++g_xserver_error_trap_level == 1) {
    g_last_xserver_error_code = 0;
    g_original_error_handler_ = XSetErrorHandler(&XServerErrorHandler);
  }
#endif  // !defined(TOOLKIT_GTK)
}

int XErrorTrap::GetLastErrorAndDisable() {
  assert(enabled_);
  enabled_ = false;
#if defined(TOOLKIT_GTK)
  return gdk_error_trap_push();
#else   // !defined(TOOLKIT_GTK)
  const auto result = g_last_xserver_error_code.load();
  if (--g_xserver_error_trap_level == 0) {
    XSetErrorHandler(g_original_error_handler_);
    g_original_error_handler_ = nullptr;
  }
  return result;
#endif  // !defined(TOOLKIT_GTK)
}

XErrorTrap::~XErrorTrap() {
  if (enabled_)
    GetLastErrorAndDisable();
}

}  // namespace webrtc
