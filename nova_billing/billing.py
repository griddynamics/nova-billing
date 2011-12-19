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


"""
This module defines strategies for accounting.
"""
from nova_billing import vm_states


BILLABLE_PARAMS_WEIGHTS = {
    'local_gb' : 1,
    'memory_mb' : 2,
    'vcpus' : 3
}


def total_seconds(td):
    """This function is added for portability 
    because timedelta.total_seconds() 
    was introduced only in python 2.7."""
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


class BasePriceCalculator(object):
    """
    Base class for simple and sophisticated price calculators.
    """

    def __call__(self, period_start, period_stop, local_gb, memory_mb, vcpus):
        raise NotImplementedError


class SimplePriceCalculator(BasePriceCalculator):
    """
    Price calculator that summarizes weighted disk, RAM, and CPU time.
    """
    def __init__(self, local_gb=0, memory_mb=0, vcpus=0):
        self.local_gb = local_gb
        self.memory_mb = memory_mb
        self.vcpus = vcpus

    def __call__(self, period_start, period_stop,
                  local_gb, memory_mb, vcpus):
        return (self.local_gb * local_gb +
                self.memory_mb * memory_mb +
                self.vcpus * vcpus
                ) * total_seconds(period_stop - period_start)


class SegmentPriceCalculator(object):
    """
    Calculator class that uses an appropriate strategy to calculate the price.
    """
    calculators = {}

    def __init__(self):
        self.calculators[vm_states.ACTIVE] = SimplePriceCalculator(
           BILLABLE_PARAMS_WEIGHTS['local_gb'],
           BILLABLE_PARAMS_WEIGHTS['memory_mb'],
           BILLABLE_PARAMS_WEIGHTS['vcpus'])
        self.calculators[vm_states.SUSPENDED] = SimplePriceCalculator(
           BILLABLE_PARAMS_WEIGHTS['local_gb'],
           BILLABLE_PARAMS_WEIGHTS['memory_mb'])
        self.calculators[vm_states.PAUSED] = SimplePriceCalculator(
           BILLABLE_PARAMS_WEIGHTS['local_gb'],
           BILLABLE_PARAMS_WEIGHTS['memory_mb'])
        self.calculators[vm_states.STOPPED] = SimplePriceCalculator(
           BILLABLE_PARAMS_WEIGHTS['local_gb'])
        self.calculators['DEFAULT'] = SimplePriceCalculator(
           BILLABLE_PARAMS_WEIGHTS['local_gb'],
           BILLABLE_PARAMS_WEIGHTS['memory_mb'],
           BILLABLE_PARAMS_WEIGHTS['vcpus'])

    def __call__(self, period_start, period_stop, state,
                  local_gb, memory_mb, vcpus):
        calc = self.calculators.get(state, self.calculators['DEFAULT'])
        return calc(period_start, period_stop, local_gb, memory_mb, vcpus)
