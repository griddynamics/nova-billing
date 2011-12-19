# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 Grid Dynamics Consulting Services, Inc, All Rights Reserved
#  http://www.griddynamics.com
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from nova_billing import vm_states


BILLABLE_PARAMS_WEIGHTS = {
    'local_gb' : 1,
    'memory_mb' : 2,
    'vcpus' : 3
}


def total_seconds(td):
    """timedelta.total_seconds() 
    that was introduced only in python 2.7"""
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


class BasePriceCalculator(object):
    price = 1

    def calculate(self, period_start, period_stop, local_gb=None, memory_mb=None, vcpus=None):
        return total_seconds(period_stop - period_start) * self.price


class ActivePriceCalculator(BasePriceCalculator):
    def calculate(self, period_start, period_stop, local_gb, memory_mb, vcpus):
        self.price += BILLABLE_PARAMS_WEIGHTS['local_gb'] * local_gb
        self.price += BILLABLE_PARAMS_WEIGHTS['memory_mb'] * memory_mb
        self.price += BILLABLE_PARAMS_WEIGHTS['vcpus'] * vcpus
        return super(ActivePriceCalculator, self).calculate(period_start, period_stop)


class SuspendedPriceCalculator(BasePriceCalculator):
    def calculate(self, period_start, period_stop, local_gb, memory_mb, vcpus):
        self.price += BILLABLE_PARAMS_WEIGHTS['local_gb'] * local_gb
        self.price += BILLABLE_PARAMS_WEIGHTS['memory_mb'] * memory_mb
        return super(SuspendedPriceCalculator, self).calculate(period_start, period_stop)


class StoppedPriceCalculator(BasePriceCalculator):
    def calculate(self, period_start, period_stop, local_gb, memory_mb, vcpus):
        self.price += BILLABLE_PARAMS_WEIGHTS['local_gb'] * local_gb
        return super(StoppedPriceCalculator, self).calculate(period_start, period_stop)


class SegmentPriceCalculator(object):
    calculators = {}

    def __init__(self):
        self.calculators[vm_states.ACTIVE] = ActivePriceCalculator()
        self.calculators[vm_states.SUSPENDED] = SuspendedPriceCalculator()
        self.calculators[vm_states.PAUSED] = SuspendedPriceCalculator()
        self.calculators[vm_states.STOPPED] = SuspendedPriceCalculator()
        self.calculators['DEFAULT'] = BasePriceCalculator()

    def calculate(self, period_start, period_stop, state,
                  local_gb, memory_mb, vcpus):
        calc = self.calculators.get(state, self.calculators['DEFAULT'])
        return calc.calculate(period_start, period_stop, local_gb, memory_mb, vcpus)
