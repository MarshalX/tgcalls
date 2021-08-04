//
//  DesktopCaptureSourceView.h
//  TgVoipWebrtc
//
//  Created by Mikhail Filimonov on 28.12.2020.
//  Copyright © 2020 Mikhail Filimonov. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
#import "tgcalls/desktop_capturer/DesktopCaptureSource.h"
#import "tgcalls/desktop_capturer/DesktopCaptureSourceHelper.h"
#import "platform/darwin/VideoMetalViewMac.h"
#import "platform/darwin/GLVideoViewMac.h"

NS_ASSUME_NONNULL_BEGIN

@interface DesktopCaptureSourceView : GLVideoView
-(id)initWithHelper:(tgcalls::DesktopCaptureSourceHelper)helper;
@end

@interface DesktopCaptureSourceScope : NSObject
-(id)initWithSource:(tgcalls::DesktopCaptureSource)source data:(tgcalls::DesktopCaptureSourceData)data;
-(NSString *)cachedKey;
@end

@interface DesktopCaptureSourceViewManager : NSObject

-(instancetype)init_s;
-(instancetype)init_w;
-(NSArray<DesktopCaptureSource *> *)list;

-(NSView *)createForScope:(DesktopCaptureSourceScope *)scope;
-(void)start:(DesktopCaptureSourceScope *)scope;
-(void)stop:(DesktopCaptureSourceScope *)scope;

@end

NS_ASSUME_NONNULL_END
