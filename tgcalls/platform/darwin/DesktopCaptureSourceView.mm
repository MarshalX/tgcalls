//
//  DesktopCaptureSourceView.m
//  TgVoipWebrtc
//
//  Created by Mikhail Filimonov on 28.12.2020.
//  Copyright © 2020 Mikhail Filimonov. All rights reserved.
//

#import "DesktopCaptureSourceView.h"
#import "platform/darwin/VideoMetalViewMac.h"

@interface DesktopCaptureSourceView ()

@end

@implementation DesktopCaptureSourceView

-(id)initWithHelper:(tgcalls::DesktopCaptureSourceHelper)helper {
    if (self = [super initWithFrame:CGRectZero]) {
        std::shared_ptr<rtc::VideoSinkInterface<webrtc::VideoFrame>> sink = [self getSink];
        helper.setOutput(sink);
        [self setVideoContentMode:kCAGravityResizeAspectFill];
    }
    return self;
}

@end

@interface DesktopCaptureSourceScope ()
-(tgcalls::DesktopCaptureSourceData)getData;
-(tgcalls::DesktopCaptureSource)getSource;
@end

@implementation DesktopCaptureSourceScope
{
    absl::optional<tgcalls::DesktopCaptureSourceData> _data;
    absl::optional<tgcalls::DesktopCaptureSource> _source;
}

-(id)initWithSource:(tgcalls::DesktopCaptureSource)source data:(tgcalls::DesktopCaptureSourceData)data {
    if (self = [super init]) {
        _data = data;
        _source = source;
    }
    return self;
}

-(tgcalls::DesktopCaptureSourceData)getData {
    return _data.value();
}
-(tgcalls::DesktopCaptureSource)getSource {
    return _source.value();
}

-(NSString *)cachedKey {
    return [[NSString alloc] initWithFormat:@"%@:%@", [NSString stringWithUTF8String:_source.value().VideoSource::uniqueKey().c_str()], [NSString stringWithUTF8String:_data.value().cachedKey().c_str()]];
}

@end

@implementation DesktopCaptureSourceViewManager
{
    std::map<NSString*, tgcalls::DesktopCaptureSourceHelper> _cached;
}

-(NSView *)createForScope:(DesktopCaptureSourceScope*)scope {
    auto i = _cached.find(scope.cachedKey);
    if (i == end(_cached)) {
        i = _cached.emplace(
            scope.cachedKey,
            tgcalls::DesktopCaptureSourceHelper([scope getSource], [scope getData])).first;
    }
    return [[DesktopCaptureSourceView alloc] initWithHelper:i->second];
}

-(void)start:(DesktopCaptureSourceScope *)scope {
    const auto i = _cached.find(scope.cachedKey);
    if (i != end(_cached)) {
        i->second.start();
    }
}

-(void)stop:(DesktopCaptureSourceScope *)scope {
    const auto i = _cached.find(scope.cachedKey);
    if (i != end(_cached)) {
        i->second.stop();
    }
}

-(void)dealloc {
    for (auto &[key, helper] : _cached) {
        helper.stop();
    }
}

@end
