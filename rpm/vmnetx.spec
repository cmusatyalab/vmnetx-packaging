%{!?_selinux_policy_version: %global _selinux_policy_version %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2>/dev/null || echo 0.0.0)}
%global selinux_variants mls targeted minimal

Name:           vmnetx
Version:        0.5.1
Release:        1%{?dist}
Summary:        Virtual machine network execution

# desktop/vmnetx.png is under CC-BY-3.0
License:        GPLv2 and CC-BY
URL:            https://github.com/cmusatyalab/vmnetx
Source0:        https://olivearchive.org/vmnetx/source/%{name}-%{version}.tar.xz

BuildRequires:  python2-devel
BuildRequires:  pkgconfig
BuildRequires:  glib2-devel
BuildRequires:  libcurl-devel
BuildRequires:  fuse-devel
BuildRequires:  libxml2-devel
# For SELinux
BuildRequires:  selinux-policy-devel
BuildRequires:  selinux-policy-doc
BuildRequires:  checkpolicy
BuildRequires:  hardlink

Requires:       %{name}-common%{?_isa} = %{version}-%{release}
Requires:       pygtk2
Requires:       spice-gtk-python
%if 0%{?rhel} == 6
# Python 2.6 doesn't have argparse in the standard library
Requires:       python-argparse
%endif


%description
VMNetX allows you to execute a KVM virtual machine over the Internet
without downloading all of its data to your computer in advance.


%package        common
Summary:        VMNetX support code
License:        GPLv2
Conflicts:      vmnetx < 0.4.0
Requires:       pygobject2
Requires:       python-lxml
Requires:       python-requests
Requires:       python-dateutil
Requires:       python-msgpack
Requires:       libvirt
Requires:       libvirt-python
Requires:       qemu-kvm
Requires:       fuse
# For authorizer
Requires:       dbus-python
Requires:       dbus
Requires:       polkit
# For SELinux
Requires:       selinux-policy >= %{_selinux_policy_version}
Requires(post): /usr/sbin/semodule
Requires(postun): /usr/sbin/semodule

%description    common
This package includes support code for VMNetX.


%package        server
Summary:        VMNetX server
License:        GPLv2
Requires:       %{name}-common%{?_isa} = %{version}-%{release}
Requires:       python-flask
Requires:       PyYAML
%if 0%{?rhel} == 6
# On RHEL 6, python-flask Requires python-jinja2-26, which does not add
# itself to the Python path, rather than python-jinja2 which does (RHBZ
# 1079599).  Flask's requirement for a newer jinja2 doesn't actually affect
# us since we don't use templating, but its inability to import jinja2
# causes the servers to crash at startup.  Work around this by explicitly
# requiring an importable jinja2.
Requires:       python-jinja2
%endif

%description    server
This package includes the VMNetX remote execution server.


%prep
%setup -q


%build
%configure --disable-update-checking
make %{?_smp_mflags}

# Build SELinux modules
for selinuxvariant in %{selinux_variants}
do
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
    mv vmnetx.pp vmnetx.pp.${selinuxvariant}
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done


%install
make install DESTDIR=$RPM_BUILD_ROOT

# Let python-devel handle byte-compiling
find $RPM_BUILD_ROOT \( -name '*.pyc' -o -name '*.pyo' \) -exec rm -f {} ';'

# Install SELinux modules
for selinuxvariant in %{selinux_variants}
do
    install -d $RPM_BUILD_ROOT%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 vmnetx.pp.${selinuxvariant} \
        $RPM_BUILD_ROOT%{_datadir}/selinux/${selinuxvariant}/vmnetx.pp
done
hardlink -cv $RPM_BUILD_ROOT%{_datadir}/selinux


%files
%doc desktop/README.icon
%{_bindir}/vmnetx
%{_bindir}/vmnetx-generate
%{_datadir}/applications/vmnetx.desktop
%{_datadir}/icons/hicolor/256x256/apps/vmnetx.png
%{_datadir}/man/man1/*
%{_datadir}/mime/packages/vmnetx.xml


%files common
%doc COPYING README.md NEWS.md
%{_sysconfdir}/dbus-1/system.d/org.olivearchive.VMNetX.Authorizer.conf
%{_libexecdir}/%{name}
%{python_sitelib}/*
%{_datadir}/dbus-1/system-services/org.olivearchive.VMNetX.Authorizer.service
%{_datadir}/polkit-1/actions/org.olivearchive.VMNetX.Authorizer.policy
%{_datadir}/selinux/*/vmnetx.pp


%files server
%{_sbindir}/vmnetx-example-frontend
%{_sbindir}/vmnetx-server
%{_datadir}/man/man8/*


%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null ||:
/usr/bin/update-mime-database %{_datadir}/mime &> /dev/null ||:
/usr/bin/update-desktop-database &> /dev/null ||:


%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null ||:
    /usr/bin/update-mime-database %{_datadir}/mime &> /dev/null ||:
    /usr/bin/update-desktop-database &> /dev/null ||:
fi


%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null ||:


%post common
for selinuxvariant in %{selinux_variants}
do
    /usr/sbin/semodule -s ${selinuxvariant} -i \
        %{_datadir}/selinux/${selinuxvariant}/vmnetx.pp &> /dev/null ||:
done


%postun common
if [ $1 -eq 0 ] ; then
    for selinuxvariant in %{selinux_variants}
    do
        /usr/sbin/semodule -s ${selinuxvariant} -r vmnetx &> /dev/null ||:
    done
fi


%changelog
* Wed Jun 03 2015 Jan Harkes <jaharkes@cs.cmu.edu> - 0.5.1-1
- New release

* Fri Oct 24 2014 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.5.0-1
- New release

* Fri May 30 2014 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.4.4-1
- New release

* Wed Mar 26 2014 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.4.3-2
- Add -server python-jinja2 dependency on EL 6 to work around RHBZ 1079599

* Tue Mar 04 2014 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.4.3-1
- New release

* Fri Dec 20 2013 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.4.2-1
- New release
- Correctly set selinux-policy version requirement on F20

* Thu Nov  7 2013 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.4.1-1
- New release

* Fri Aug 30 2013 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.4.0-2
- Move python-msgpack dependency to -common (fixes thin client mode)

* Wed Aug 28 2013 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.4.0-1
- New release
- Add -common and -server subpackages

* Fri Jun 21 2013 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.3.3-1
- New release

* Fri Apr 26 2013 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.3.2-1
- New release

* Mon Apr 22 2013 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.3.1-1
- New release

* Wed Apr 10 2013 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.3-1
- New release
- Update package and source URLs

* Sun Apr 08 2012 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.2-1
- Initial release
