# -*- mode: python -*-

block_cipher = None


a = Analysis(['nzbhydra.py'],
             pathex=[''],
             binaries=None,
             datas=[('templates', 'templates'), 
                    ('static', 'static'), 
                    ('data', 'data'),
                    ('README.md', '.'),
                    ('version.txt', '.'),
                    ('LICENSE', '.'),
                    ('nzbhydra.key', '.'),
                    ('nzbhydra.crt', '.')],
             hiddenimports=["rison"],
             hookspath=None,
             
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          icon='ui-src/img/favicon.ico',
          name='nzbhydra',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='nzbhydra')
