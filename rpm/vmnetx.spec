%global selinux_policyver %(%{__sed} -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2>/dev/null || echo 0.0.0)
%global selinux_variants mls targeted minimal

Name:           vmnetx
Version:        0.1
Release:        1%{?dist}
Summary:        Virtual machine network execution

License:        GPLv2
URL:            https://github.com/vmnetx/vmnetx
Source0:        %{name}-%{version}.tar.xz

BuildRequires:  python2-devel
BuildRequires:  pkgconfig
BuildRequires:  glib2-devel
BuildRequires:  libcurl-devel
BuildRequires:  fuse-devel
# For SELinux
BuildRequires:  selinux-policy-devel
BuildRequires:  selinux-policy-doc
BuildRequires:  checkpolicy
BuildRequires:  hardlink

Requires:       pygtk2
Requires:       gtk-vnc-python
Requires:       python-lxml
Requires:       libvirt
Requires:       libvirt-python
Requires:       qemu-kvm
# For SELinux
Requires:       libselinux-python
Requires:       selinux-policy >= %{selinux_policyver}
Requires(post): /usr/sbin/semodule
Requires(postun): /usr/sbin/semodule


%description
VMNetX allows you to execute a KVM virtual machine over the Internet
without downloading all of its data to your computer in advance.


%prep
%setup -q


%build
%configure
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
%doc COPYING README.rst
%{_bindir}/vmnetx
%{_bindir}/vmnetx-generate
%{_libexecdir}/%{name}
%{python_sitelib}/*
%{_datadir}/applications/vmnetx.desktop
%{_datadir}/mime/packages/vmnetx.xml
%{_datadir}/selinux/*/vmnetx.pp


%post
for selinuxvariant in %{selinux_variants}
do
    /usr/sbin/semodule -s ${selinuxvariant} -i \
        %{_datadir}/selinux/${selinuxvariant}/vmnetx.pp &> /dev/null ||:
done
/usr/bin/update-mime-database %{_datadir}/mime &> /dev/null ||:
/usr/bin/update-desktop-database &> /dev/null ||:


%postun
if [ $1 -eq 0 ] ; then
    for selinuxvariant in %{selinux_variants}
    do
        /usr/sbin/semodule -s ${selinuxvariant} -r vmnetx &> /dev/null ||:
    done
    /usr/bin/update-mime-database %{_datadir}/mime &> /dev/null ||:
    /usr/bin/update-desktop-database &> /dev/null ||:
fi


%changelog
* Sun Apr 08 2012 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 0.1-1
- Initial release
