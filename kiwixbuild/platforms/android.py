from .base import PlatformInfo, MetaPlatformInfo
from kiwixbuild.utils import pj
from kiwixbuild._global import get_target_step, option


class AndroidPlatformInfo(PlatformInfo):
    build = 'android'
    static = True
    toolchain_names = ['android-ndk']
    compatible_hosts = ['fedora', 'debian']

    def __str__(self):
        return "android"

    @property
    def binaries_name(self):
        arch_full = self.arch_full
        return {
          'CC': '{}{}-{}'.format(arch_full, self.api, 'clang'),
          'CXX': '{}{}-{}'.format(arch_full, self.api, 'clang++'),
          'AR': '{}-{}'.format(arch_full, 'ar'),
          'STRIP': '{}-{}'.format(arch_full, 'strip'),
          'RANLIB': '{}-{}'.format(arch_full, 'ranlib'),
          'LD': '{}-{}'.format(arch_full, 'ld')
        }

    def binaries(self):
        install_path = self.install_path
        return {k:pj(install_path, 'bin', v)
                for k,v in self.binaries_name.items()}

    @property
    def ndk_source(self):
        return get_target_step('android-ndk', 'source')

    @property
    def install_path(self):
        return pj(self.ndk_source.source_path, 'toolchains', 'llvm', 'prebuilt', 'linux-x86_64')

    def get_cross_config(self):
        return {
            'exec_wrapper_def': '',
            'install_path': self.install_path,
            'binaries': self.binaries(),
            'root_path': pj(self.install_path, 'sysroot'),
            'extra_libs': ['-llog'],
            'extra_cflags': ['-I{}'.format(pj(self.buildEnv.install_dir, 'include'))],
            'host_machine': {
                'system': 'Android',
                'lsystem': 'android',
                'cpu_family': self.arch,
                'cpu': self.cpu,
                'endian': 'little',
                'abi': self.abi
            },
        }

    def get_bin_dir(self):
        return [pj(self.install_path, 'bin')]

    def set_env(self, env):
        root_path = pj(self.install_path, 'sysroot')
        env['PKG_CONFIG_LIBDIR'] = pj(root_path, 'lib', 'pkgconfig')
        env['CFLAGS'] = '-fPIC --sysroot={} '.format(root_path) + env['CFLAGS']
        env['CXXFLAGS'] = '-fPIC --sysroot={} '.format(root_path) + env['CXXFLAGS']
        env['LDFLAGS'] = '--sysroot={} '.format(root_path) + env['LDFLAGS']
        #env['CFLAGS'] = ' -fPIC -D_FILE_OFFSET_BITS=64 -O3 '+env['CFLAGS']
        #env['CXXFLAGS'] = (' -D__OPTIMIZE__ -fno-strict-aliasing '
        #                   ' -DU_HAVE_NL_LANGINFO_CODESET=0 '
        #                   '-DU_STATIC_IMPLEMENTATION -O3 '
        #                   '-DU_HAVE_STD_STRING -DU_TIMEZONE=0 ')+env['CXXFLAGS']
        env['NDK_DEBUG'] = '0'

    def set_compiler(self, env):
        binaries = self.binaries()
        for k,v in binaries.items():
            env[k] = v

    @property
    def configure_option(self):
        return '--host={}'.format(self.arch_full)

    def finalize_setup(self):
        super().finalize_setup()
        self.buildEnv.cmake_crossfile = self._gen_crossfile('cmake_android_cross_file.txt')
        self.buildEnv.meson_crossfile = self._gen_crossfile('meson_cross_file.txt')


class AndroidArm(AndroidPlatformInfo):
    name = 'android_arm'
    arch = cpu = 'arm'
    arch_full = 'armv7a-linux-androideabi'
    abi = 'armeabi-v7a'
    api = '24'

    @property
    def binaries_name(self):
        names = super().binaries_name
        for bin in ('AR', 'STRIP', 'RANLIB', 'LD'):
            names[bin] = 'arm-linux-androideabi-{}'.format(bin.lower())
        return names


class AndroidArm64(AndroidPlatformInfo):
    name = 'android_arm64'
    arch = 'arm64'
    arch_full = 'aarch64-linux-android'
    cpu = 'aarch64'
    abi = 'arm64-v8a'
    api = '21'


class AndroidX86(AndroidPlatformInfo):
    name = 'android_x86'
    arch = abi = 'x86'
    arch_full = 'i686-linux-android'
    cpu = 'i686'
    api = '24'


class AndroidX8664(AndroidPlatformInfo):
    name = 'android_x86_64'
    arch = cpu = abi = 'x86_64'
    arch_full = 'x86_64-linux-android'
    api = '21'


class Android(MetaPlatformInfo):
    name = "android"
    toolchain_names = ['android-sdk', 'gradle']
    compatible_hosts = ['fedora', 'debian']

    @property
    def subPlatformNames(self):
        return ['android_{}'.format(arch) for arch in option('android_arch')]

    def add_targets(self, targetName, targets):
        if targetName not in ('kiwix-android', 'kiwix-android-custom'):
            return super().add_targets(targetName, targets)
        else:
            return AndroidPlatformInfo.add_targets(self, targetName, targets)

    def __str__(self):
        return self.name

    @property
    def sdk_builder(self):
        return get_target_step('android-sdk', 'neutral')

    @property
    def gradle_builder(self):
        return get_target_step('gradle', 'neutral')

    def set_env(self, env):
        env['ANDROID_HOME'] = self.sdk_builder.install_path
        env['PATH'] = ':'.join([pj(self.gradle_builder.install_path, 'bin'), env['PATH']])
