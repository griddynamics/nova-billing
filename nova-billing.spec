%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%endif

%define mod_name nova_billing

Name:             nova-billing
Version:          0.0.2
Release:          1
Summary:          A nova billing server
License:          GNU GPL v3
Vendor:           Grid Dynamics International, Inc.
URL:              http://www.griddynamics.com/openstack
Group:            Development/Languages/Python

Source0:          %{name}-%{version}.tar.gz
BuildRoot:        %{_tmppath}/%{name}-%{version}-build
BuildRequires:    python-devel python-setuptools make 
BuildArch:        noarch
Requires:         openstack-nova
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
BuildRequires:  python-sphinx

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
install -p -D -m 755 redhat/nova-billing.init %{buildroot}%{_initrddir}/%{name}

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
%doc README
%{_initrddir}/*
%{python_sitelib}/%{mod_name}*
%{_usr}/bin/*

%files doc
%defattr(-,root,root,-)
%doc doc/build/html

%changelog
