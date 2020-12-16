#include "RtcServer.h"

using namespace std;

RtcServer::RtcServer(string ip, string ipv6, int port, string login, string password, bool isTurn, bool isStun):
        ip(move(ip)), ipv6(move(ipv6)), port(port), login(move(login)), password(move(password)),
        isTurn(isTurn), isStun(isStun)
{
}

tgcalls::RtcServer RtcServer::toTgcalls(bool asIpv6, bool supportTurn) {
    tgcalls::RtcServer rtcServer;

    if (asIpv6) {
        rtcServer.host = ipv6;
    } else {
        rtcServer.host = ip;
    }

    if (supportTurn) {
        rtcServer.login = login;
        rtcServer.password = password;
    }

    rtcServer.port = static_cast<uint16_t>(port);
    rtcServer.isTurn = supportTurn;

    return rtcServer;
};
