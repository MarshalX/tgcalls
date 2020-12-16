#pragma once

#include <tgcalls/Instance.h>

using namespace std;

struct RtcServer
{
    RtcServer(string ip, string ipv6, int port, string login, string password, bool isTurn, bool isStun);
    tgcalls::RtcServer toTgcalls(bool asIpv6 = false, bool supportTurn = true);

    string ip;
    string ipv6;
    int port;
    string login;
    string password;
    bool isTurn;
    bool isStun;
};
