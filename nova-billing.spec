%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%endif

%define mod_name nova_billing

Name:             nova-billing
Version:          2.0.0
Release:          1
Summary:          A common billing server
License:          GNU GPL v3
Vendor:           Grid Dynamics International, Inc.
URL:              http://www.griddynamics.com/openstack
Group:            Development/Languages/Python

Source0:          %{name}-%{version}.tar.gz
BuildRoot:        %{_tmppath}/%{name}-%{version}-build
BuildRequires:    python-devel python-setuptools make
BuildArch:        noarch
Requires:         python-flask python-flask-sqlalchemy
Requires:         start-stop-daemon

%description
Nova is a cloud computing fabric controller (the main part of an IaaS system)
built to match the popular AWS EC2 and S3 APIs. It is written in Python, using
the Tornado and Twisted frameworks, and relies on the standard AMQP messaging
protocol, and the Redis KVS.

This package contains the nova billing server.


%package doc
Summary:        Documentation for %{name}
Group:          Documentation
Requires:       %{name} = %{version}-%{release}
BuildRequires:  python-sphinx make

%description doc
Documentation and examples for %{name}.


%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
%__rm -rf %{buildroot}

%{__python} setup.py install -O1 --skip-build --prefix=%{_prefix} --root=%{buildroot}
export PYTHONPATH=%{buildroot}%{python_sitelib}
make -C doc html
cd redhat
for script in *.init; do
    install -p -D -m 755 "$script" "%{buildroot}%{_initrddir}/${script%.init}"
done
cd ..
mkdir -p %{buildroot}/etc
cp -a etc/nova-billing %{buildroot}/etc
mkdir -p %{buildroot}%{_localstatedir}/{log,lib,run}/nova-billing


%clean
%__rm -rf %{buildroot}


%pre
getent group nova-billing >/dev/null || groupadd -r nova-billing
getent passwd nova-billing >/dev/null || \
useradd -r -g nova-billing -d %{_sharedstatedir}/nova-billing -s /sbin/nologin \
-c "Nova Billing Daemons" nova-billing
exit 0


%preun
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}-heart
    /sbin/chkconfig --del %{name}-os-amqp
fi
exit 0


%postun
if [ $1 -eq 1 ] ; then
    /sbin/service %{name}-heart condrestart
    /sbin/service %{name}-os-amqp condrestart
fi
exit 0


%files
%defattr(-,root,root,-)
%doc README.rst
%{_initrddir}/*
%{python_sitelib}/%{mod_name}*
%{_usr}/bin/*
%config(noreplace) /etc/nova-billing

%defattr(0775,nova-billing,nova-billing,-)
%dir %{_sharedstatedir}/nova-billing
%dir %{_localstatedir}/log/nova-billing
%dir %{_localstatedir}/run/nova-billing


%files doc
%defattr(-,root,root,-)
%doc doc/build/html

%changelog
