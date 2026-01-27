import { useState } from 'react';
import { ShoppingCart, Check, Zap, Building2, User } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

interface PricingTier {
  id: string;
  name: string;
  icon: typeof User;
  description: string;
  price: string;
  priceMonthly?: string;
  features: string[];
  highlighted?: boolean;
}

const pricingTiers: PricingTier[] = [
  {
    id: 'trial',
    name: 'Free Trial',
    icon: Zap,
    description: '14-day trial with limited features',
    price: '$0',
    features: [
      '50 scans per day',
      'AI-powered malware analysis',
      'Basic real-time protection',
      'Email support',
      'Single device',
    ],
  },
  {
    id: 'personal',
    name: 'Personal',
    icon: User,
    description: 'Perfect for individual users',
    price: '$49',
    priceMonthly: '$4.99/month billed annually',
    features: [
      'Unlimited scans',
      'AI-powered malware analysis',
      'Full real-time protection',
      'Cloud quarantine backup',
      'Priority email support',
      'Single device',
    ],
  },
  {
    id: 'professional',
    name: 'Professional',
    icon: Zap,
    description: 'For power users and developers',
    price: '$99',
    priceMonthly: '$9.99/month billed annually',
    highlighted: true,
    features: [
      'Everything in Personal',
      'Up to 3 devices',
      'Advanced threat detection',
      'Custom YARA rules',
      'API access',
      'Priority support (24/7)',
      'Team license management',
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    icon: Building2,
    description: 'For businesses and organizations',
    price: 'Contact Us',
    features: [
      'Everything in Professional',
      'Up to 10 devices',
      'Dedicated account manager',
      'Custom integrations',
      'SLA guarantee',
      'On-premise deployment option',
      'Training and onboarding',
    ],
  },
];

export default function Purchase() {
  const [loading, setLoading] = useState<string | null>(null);

  const handlePurchase = async (tierId: string) => {
    if (tierId === 'enterprise') {
      window.open('mailto:sales@hifzdefend.com?subject=Enterprise License Inquiry', '_blank');
      return;
    }

    setLoading(tierId);

    try {
      // Get user email (in real app, would be from auth)
      const email = prompt('Enter your email address:');
      if (!email) {
        setLoading(null);
        return;
      }

      // Create checkout session
      const response = await fetch('/api/v1/payments/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_email: email,
          license_type: tierId,
          success_url: `${window.location.origin}/license?success=true`,
          cancel_url: `${window.location.origin}/purchase?canceled=true`,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create checkout session');
      }

      const data = await response.json();

      // Redirect to Stripe checkout
      window.location.href = data.checkout_url;
    } catch (error) {
      console.error('Purchase failed:', error);
      alert(
        'Payment system is not yet configured. This is a demo feature.\n\n' +
        'In production, this would redirect to Stripe checkout.'
      );
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Choose Your Plan
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400">
          Protect your system with HifzDefend's advanced AI-powered antivirus
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {pricingTiers.map((tier) => (
          <Card
            key={tier.id}
            className={
              tier.highlighted
                ? 'border-2 border-blue-500 shadow-lg relative'
                : ''
            }
          >
            {tier.highlighted && (
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                  MOST POPULAR
                </span>
              </div>
            )}

            <CardHeader>
              <div className="flex items-center justify-between mb-4">
                <tier.icon className="w-8 h-8 text-blue-600" />
                {tier.highlighted && (
                  <Check className="w-6 h-6 text-green-500" />
                )}
              </div>
              <CardTitle>{tier.name}</CardTitle>
              <CardDescription>{tier.description}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">
                  {tier.price}
                  {tier.price !== 'Contact Us' && tier.id !== 'trial' && (
                    <span className="text-lg font-normal text-gray-500">/year</span>
                  )}
                </div>
                {tier.priceMonthly && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {tier.priceMonthly}
                  </p>
                )}
              </div>

              <ul className="space-y-2">
                {tier.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <Button
                onClick={() => handlePurchase(tier.id)}
                disabled={loading !== null}
                className="w-full"
                variant={tier.highlighted ? 'default' : 'outline'}
              >
                {loading === tier.id ? (
                  'Loading...'
                ) : tier.id === 'trial' ? (
                  'Start Free Trial'
                ) : tier.id === 'enterprise' ? (
                  'Contact Sales'
                ) : (
                  <>
                    <ShoppingCart className="w-4 h-4 mr-2" />
                    Purchase Now
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-12 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          All Plans Include:
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700 dark:text-gray-300">
          <div className="flex items-center">
            <Check className="w-4 h-4 text-green-500 mr-2" />
            ClamAV virus engine
          </div>
          <div className="flex items-center">
            <Check className="w-4 h-4 text-green-500 mr-2" />
            Behavioral monitoring
          </div>
          <div className="flex items-center">
            <Check className="w-4 h-4 text-green-500 mr-2" />
            Quarantine management
          </div>
          <div className="flex items-center">
            <Check className="w-4 h-4 text-green-500 mr-2" />
            Automatic updates
          </div>
          <div className="flex items-center">
            <Check className="w-4 h-4 text-green-500 mr-2" />
            Web dashboard
          </div>
          <div className="flex items-center">
            <Check className="w-4 h-4 text-green-500 mr-2" />
            30-day money-back guarantee
          </div>
        </div>
      </div>
    </div>
  );
}
