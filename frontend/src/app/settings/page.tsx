'use client'

import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { settingsAPI } from '@/lib/api/client'
import { useToastStore } from '@/lib/store'
import { Save, Key, Settings2, Bell, DollarSign, CheckCircle2, XCircle } from 'lucide-react'

export default function SettingsPage() {
  const addToast = useToastStore((state) => state.addToast)

  const { data: settings, refetch } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsAPI.get(),
  })

  const [apiKeys, setApiKeys] = useState({
    anthropic: '',
    openai: '',
    google: '',
    ahrefs: '',
  })

  const [defaults, setDefaults] = useState({
    llm_provider: 'auto',
    strategy: 'multi_stage',
    country: 'se',
  })

  const [costLimits, setCostLimits] = useState({
    enabled: false,
    daily_limit_usd: 10,
    per_job_limit_usd: 1,
  })

  const updateMutation = useMutation({
    mutationFn: (data: any) => settingsAPI.update(data),
    onSuccess: () => {
      addToast({
        type: 'success',
        title: 'Settings Saved',
        message: 'Your settings have been updated',
      })
      refetch()
    },
    onError: () => {
      addToast({
        type: 'error',
        title: 'Failed to Save',
        message: 'Could not update settings',
      })
    },
  })

  const testKeyMutation = useMutation({
    mutationFn: ({ provider, key }: { provider: string; key: string }) =>
      settingsAPI.testAPIKey(provider, key),
  })

  const handleSaveAPIKeys = () => {
    updateMutation.mutate({ api_keys: apiKeys })
  }

  const handleSaveDefaults = () => {
    updateMutation.mutate({ defaults })
  }

  const handleSaveCostLimits = () => {
    updateMutation.mutate({ cost_limits: costLimits })
  }

  const handleTestKey = async (provider: string) => {
    const key = apiKeys[provider as keyof typeof apiKeys]
    if (!key) return

    try {
      const valid = await testKeyMutation.mutateAsync({ provider, key })
      addToast({
        type: valid ? 'success' : 'error',
        title: valid ? 'Valid Key' : 'Invalid Key',
        message: valid
          ? `${provider} API key is valid`
          : `${provider} API key is invalid`,
      })
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Test Failed',
        message: 'Could not test API key',
      })
    }
  }

  React.useEffect(() => {
    if (settings) {
      setApiKeys({
        anthropic: settings.api_keys?.anthropic || '',
        openai: settings.api_keys?.openai || '',
        google: settings.api_keys?.google || '',
        ahrefs: settings.api_keys?.ahrefs || '',
      })
      setDefaults({
        llm_provider: settings.defaults?.llm_provider || 'auto',
        strategy: settings.defaults?.strategy || 'multi_stage',
        country: settings.defaults?.country || 'se',
      })
      setCostLimits({
        enabled: settings.cost_limits?.enabled || false,
        daily_limit_usd: settings.cost_limits?.daily_limit_usd || 10,
        per_job_limit_usd: settings.cost_limits?.per_job_limit_usd || 1,
      })
    }
  }, [settings])

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your API keys, defaults, and preferences
        </p>
      </div>

      <Tabs defaultValue="api-keys" className="space-y-4">
        <TabsList>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          <TabsTrigger value="defaults">Defaults</TabsTrigger>
          <TabsTrigger value="cost-limits">Cost Limits</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        {/* API Keys Tab */}
        <TabsContent value="api-keys">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Key className="h-5 w-5 text-primary" />
                <CardTitle>API Keys</CardTitle>
              </div>
              <CardDescription>
                Configure your LLM and SERP API keys
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Anthropic */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">Anthropic Claude</label>
                  <Badge variant={apiKeys.anthropic ? 'success' : 'secondary'}>
                    {apiKeys.anthropic ? 'Configured' : 'Not Set'}
                  </Badge>
                </div>
                <div className="flex gap-2">
                  <Input
                    type="password"
                    placeholder="sk-ant-..."
                    value={apiKeys.anthropic}
                    onChange={(e) =>
                      setApiKeys({ ...apiKeys, anthropic: e.target.value })
                    }
                  />
                  <Button
                    variant="outline"
                    onClick={() => handleTestKey('anthropic')}
                    disabled={!apiKeys.anthropic}
                  >
                    Test
                  </Button>
                </div>
              </div>

              {/* OpenAI */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">OpenAI GPT</label>
                  <Badge variant={apiKeys.openai ? 'success' : 'secondary'}>
                    {apiKeys.openai ? 'Configured' : 'Not Set'}
                  </Badge>
                </div>
                <div className="flex gap-2">
                  <Input
                    type="password"
                    placeholder="sk-..."
                    value={apiKeys.openai}
                    onChange={(e) =>
                      setApiKeys({ ...apiKeys, openai: e.target.value })
                    }
                  />
                  <Button
                    variant="outline"
                    onClick={() => handleTestKey('openai')}
                    disabled={!apiKeys.openai}
                  >
                    Test
                  </Button>
                </div>
              </div>

              {/* Google */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">Google Gemini</label>
                  <Badge variant={apiKeys.google ? 'success' : 'secondary'}>
                    {apiKeys.google ? 'Configured' : 'Not Set'}
                  </Badge>
                </div>
                <div className="flex gap-2">
                  <Input
                    type="password"
                    placeholder="..."
                    value={apiKeys.google}
                    onChange={(e) =>
                      setApiKeys({ ...apiKeys, google: e.target.value })
                    }
                  />
                  <Button
                    variant="outline"
                    onClick={() => handleTestKey('google')}
                    disabled={!apiKeys.google}
                  >
                    Test
                  </Button>
                </div>
              </div>

              {/* Ahrefs */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">Ahrefs (Optional)</label>
                  <Badge variant={apiKeys.ahrefs ? 'success' : 'secondary'}>
                    {apiKeys.ahrefs ? 'Configured' : 'Not Set'}
                  </Badge>
                </div>
                <div className="flex gap-2">
                  <Input
                    type="password"
                    placeholder="..."
                    value={apiKeys.ahrefs}
                    onChange={(e) =>
                      setApiKeys({ ...apiKeys, ahrefs: e.target.value })
                    }
                  />
                  <Button
                    variant="outline"
                    onClick={() => handleTestKey('ahrefs')}
                    disabled={!apiKeys.ahrefs}
                  >
                    Test
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Without Ahrefs, mock SERP data will be used
                </p>
              </div>

              <Button onClick={handleSaveAPIKeys} className="w-full">
                <Save className="h-4 w-4 mr-2" />
                Save API Keys
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Defaults Tab */}
        <TabsContent value="defaults">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Settings2 className="h-5 w-5 text-primary" />
                <CardTitle>Default Settings</CardTitle>
              </div>
              <CardDescription>
                Set default values for new jobs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  LLM Provider
                </label>
                <select
                  className="w-full h-10 rounded-md border border-input bg-background px-3"
                  value={defaults.llm_provider}
                  onChange={(e) =>
                    setDefaults({ ...defaults, llm_provider: e.target.value })
                  }
                >
                  <option value="auto">Auto</option>
                  <option value="anthropic">Claude</option>
                  <option value="openai">GPT</option>
                  <option value="google">Gemini</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Writing Strategy
                </label>
                <select
                  className="w-full h-10 rounded-md border border-input bg-background px-3"
                  value={defaults.strategy}
                  onChange={(e) =>
                    setDefaults({ ...defaults, strategy: e.target.value })
                  }
                >
                  <option value="multi_stage">Multi-Stage</option>
                  <option value="single_shot">Single-Shot</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Country</label>
                <Input
                  placeholder="se"
                  value={defaults.country}
                  onChange={(e) =>
                    setDefaults({ ...defaults, country: e.target.value })
                  }
                />
              </div>

              <Button onClick={handleSaveDefaults} className="w-full">
                <Save className="h-4 w-4 mr-2" />
                Save Defaults
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cost Limits Tab */}
        <TabsContent value="cost-limits">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-primary" />
                <CardTitle>Cost Limits</CardTitle>
              </div>
              <CardDescription>
                Set spending limits to control costs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Enable Cost Limits</p>
                  <p className="text-sm text-muted-foreground">
                    Prevent overspending by setting limits
                  </p>
                </div>
                <Button
                  variant={costLimits.enabled ? 'default' : 'outline'}
                  onClick={() =>
                    setCostLimits({ ...costLimits, enabled: !costLimits.enabled })
                  }
                >
                  {costLimits.enabled ? 'Enabled' : 'Disabled'}
                </Button>
              </div>

              {costLimits.enabled && (
                <>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Daily Limit (USD)
                    </label>
                    <Input
                      type="number"
                      step="0.01"
                      value={costLimits.daily_limit_usd}
                      onChange={(e) =>
                        setCostLimits({
                          ...costLimits,
                          daily_limit_usd: parseFloat(e.target.value),
                        })
                      }
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Per Job Limit (USD)
                    </label>
                    <Input
                      type="number"
                      step="0.01"
                      value={costLimits.per_job_limit_usd}
                      onChange={(e) =>
                        setCostLimits({
                          ...costLimits,
                          per_job_limit_usd: parseFloat(e.target.value),
                        })
                      }
                    />
                  </div>
                </>
              )}

              <Button onClick={handleSaveCostLimits} className="w-full">
                <Save className="h-4 w-4 mr-2" />
                Save Cost Limits
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" />
                <CardTitle>Notifications</CardTitle>
              </div>
              <CardDescription>
                Configure email and webhook notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center py-8 text-muted-foreground">
                <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Notifications coming soon!</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
