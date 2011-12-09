%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%endif

%define mod_name nova_billing

Name:             openstack-nova-billing
Version:          2011.3
Release:          3
Summary:          A nova billing server
License:          Apache 2.0
Vendor:           Grid Dynamics Consulting Services, Inc.
Group:            Development/Languages/Python

Source0:          %{name}-%{version}.tar.gz
BuildRoot:        %{_tmppath}/%{name}-%{version}-build
BuildRequires:    python-devel python-setuptools
BuildArch:        noarch
Requires:         openstack-nova
Requires:         start-stop-daemon

%description
Nova is a cloud computing fabric controller (the main part of an IaaS system)
built to match the popular AWS EC2 and S3 APIs. It is written in Python, using
the Tornado and Twisted frameworks, and relies on the standard AMQP messaging
protocol, and the Redis KVS.

This package contains the nova billing server.

%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
%__rm -rf %{buildroot}

%{__python} setup.py install -O1 --skip-build --prefix=%{_prefix} --root=%{buildroot}

install -p -D -m 755 redhat/openstack-nova-billing.init %{buildroot}%{_initrddir}/%{name}

%clean
%__rm -rf %{buildroot}

%post
/sbin/chkconfig --add %{name}

%preun
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi

%postun
if [ $1 -eq 1 ] ; then
    /sbin/service %{name} condrestart
fi

%files
%defattr(-,root,root,-)
%{_initrddir}/*
%{python_sitelib}/%{mod_name}*
%{_usr}/bin/*

%changelog
