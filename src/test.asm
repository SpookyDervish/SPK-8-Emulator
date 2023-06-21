.data
messageone: "!==== SPK-8 FIRMWARE ====!\n"
.text
mov 0x07, eax, 4
mov 0x07, ebx, 1
mov 0x07, edx, 27
int 0x80
uld
.data
messagetwo: "Searching for bootable medium....\n"
.text
mov 0x07, edx, 34
int 0x80
uld