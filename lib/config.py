__api_version__ = 24
salt = b'=\xdc\xee\xf2.\xfaa\xc9\xa3\xc5\xf7\xf8,Z\xcfw\x06\x92\xcc/|\xfa\xd8\xfa\xa4\xcf\xe1\x8e\x8b\xdb\x1b\xbf'

package_dict = {
    'request': {
        'header': {'format': '<16sBHI', 'keys': ('client_id', 'version', 'code', 'payload_size'), 'types': (str, int, int, int)},
        'payload': {
            # KDC
            '1024': {'format': '<255s255s', 'keys': ('name', 'password'), 'types': (str, str)},
            '1025': {'format': '<255s32s16sH', 'keys': ('name', 'aes_key', 'server_ip', 'server_port'), 'types': (str, bytes, str, int)},
            '1026': None,
            '1027': {'format': '<16s8s', 'keys': ('server_id', 'nonce'), 'types': (str, int)},

            # MSG Server
            '1028': {'format': '<16s16s32s32s32sB16s16sf16s48s16s',
                     'keys': ('authenticator__auth_iv', 'authenticator__version', 'authenticator__client_id', 'authenticator__server_id', 'authenticator__timestamp', 'ticket__version', 'ticket__client_id', 'ticket__server_id', 'ticket__timestamp', 'ticket__ticket_iv', 'ticket__aes_key', 'ticket__expiration_time'),
                     'types': (bytes, bytes, bytes, bytes, bytes, int, str, str, float, bytes, bytes, bytes)},
            '1029': {'format': '<I16s', 'is_last_item_has_unknown_size': True, 'keys': ('message_size', 'iv', 'message_content'), 'types': (bytes, bytes, bytes)}, # FIXME: Need to take care of very long messages, what is the format ?
        },
    }, 'response': {
        'header': {'format': '<BHI', 'keys': ('version', 'code', 'payload_size'), 'types': (int, int, int)},
        'payload': {
            # KDC
            '16000': {'format': '<16s', 'keys': ('server_id',), 'types': (str,)},
            '1600': {'format': '<16s', 'keys': ('client_id',), 'types': (str,)},
            '1601': None,
            '1602': {'format': '<16s255s16sH', 'keys': ('server_id', 'name', 'server_ip', 'server_port'), 'is_list': True, 'types': (str, str, str, int)},
            '1603': {'format': '<16s16s16s48sB16s16sf16s48s16s',  # FIXME I changed the number of AES KEYS TO 48
                     'keys': ('client_id', 'symmetric_key__symm_iv', 'symmetric_key__nonce', 'symmetric_key__aes_key', 'ticket__version', 'ticket__client_id', 'ticket__server_id', 'ticket__timestamp', 'ticket__ticket_iv', 'ticket__aes_key', 'ticket__expiration_time'),
                     'types': (str, bytes, bytes, bytes, int, str, str, float, bytes, bytes, bytes)
                     },

            # MSG Server
            '1604': None,
            '1605': None,
            '1609': None,
        },
    }
}
