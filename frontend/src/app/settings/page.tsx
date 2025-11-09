'use client'

import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { settingsAPI, notificationsAPI } from '@/lib/api/client'
import { useToastStore } from '@/lib/store'
import { Save, Key, Settings2, Bell, DollarSign, CheckCircle2, XCircle, Mail, Webhook, Send } from 'lucide-react'
import { Switch } from '@/components/ui/switch'

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

  const [notifications, setNotifications] = useState({
    notification_email: '',
    webhook_url: '',
    enable_email_notifications: false,
    enable_webhook_notifications: false,
  })

  // Fetch notification preferences
  const { data: notificationPrefs, refetch: refetchNotifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsAPI.get(),
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

  const updateNotificationsMutation = useMutation({
    mutationFn: (data: any) => notificationsAPI.update(data),
    onSuccess: () => {
      addToast({
        type: 'success',
        title: 'Notifications Updated',
        message: 'Your notification preferences have been saved',
      })
      refetchNotifications()
    },
    onError: (error: any) => {
      addToast({
        type: 'error',
        title: 'Failed to Update',
        message: error.details?.detail || 'Could not update notification preferences',
      })
    },
  })

  const testEmailMutation = useMutation({
    mutationFn: () => notificationsAPI.testEmail(),
    onSuccess: (data) => {
      addToast({
        type: 'success',
        title: 'Test Email Sent',
        message: data.message,
      })
    },
    onError: (error: any) => {
      addToast({
        type: 'error',
        title: 'Failed to Send',
        message: error.details?.detail || 'Could not send test email',
      })
    },
  })

  const testWebhookMutation = useMutation({
    mutationFn: () => notificationsAPI.testWebhook(),
    onSuccess: (data) => {
      addToast({
        type: 'success',
        title: 'Test Webhook Sent',
        message: data.message,
      })
    },
    onError: (error: any) => {
      addToast({
        type: 'error',
        title: 'Failed to Send',
        message: error.details?.detail || 'Could not send test webhook',
      })
    },
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

  const handleSaveNotifications = () => {
    updateNotificationsMutation.mutate(notifications)
  }

  const handleTestEmail = () => {
    testEmailMutation.mutate()
  }

  const handleTestWebhook = () => {
    testWebhookMutation.mutate()
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

  React.useEffect(() => {
    if (notificationPrefs) {
      setNotifications({
        notification_email: notificationPrefs.notification_email || '',
        webhook_url: notificationPrefs.webhook_url || '',
        enable_email_notifications: notificationPrefs.enable_email_notifications || false,
        enable_webhook_notifications: notificationPrefs.enable_webhook_notifications || false,
      })
    }
  }, [notificationPrefs])

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
          <div className="space-y-4">
            {/* Email Notifications */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-primary" />
                  <CardTitle>Email Notifications</CardTitle>
                </div>
                <CardDescription>
                  Receive email notifications when jobs complete or encounter errors
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="space-y-0.5">
                    <div className="font-medium">Enable Email Notifications</div>
                    <div className="text-sm text-muted-foreground">
                      Get notified via email for job completion and errors
                    </div>
                  </div>
                  <Switch
                    checked={notifications.enable_email_notifications}
                    onCheckedChange={(checked) =>
                      setNotifications({
                        ...notifications,
                        enable_email_notifications: checked,
                      })
                    }
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Notification Email
                  </label>
                  <Input
                    type="email"
                    placeholder="alerts@example.com"
                    value={notifications.notification_email}
                    onChange={(e) =>
                      setNotifications({
                        ...notifications,
                        notification_email: e.target.value,
                      })
                    }
                    disabled={!notifications.enable_email_notifications}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Can be different from your login email
                  </p>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={handleTestEmail}
                    disabled={
                      !notifications.enable_email_notifications ||
                      !notifications.notification_email ||
                      testEmailMutation.isPending
                    }
                  >
                    <Send className="h-4 w-4 mr-2" />
                    {testEmailMutation.isPending ? 'Sending...' : 'Send Test Email'}
                  </Button>
                </div>

                {notifications.enable_email_notifications && notifications.notification_email && (
                  <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <div className="flex gap-2">
                      <CheckCircle2 className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-blue-900 dark:text-blue-100">
                        <strong>Email notifications active</strong>
                        <p className="text-blue-700 dark:text-blue-300 mt-1">
                          You'll receive notifications at <strong>{notifications.notification_email}</strong> when jobs complete or encounter errors.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Webhook Notifications */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Webhook className="h-5 w-5 text-primary" />
                  <CardTitle>Webhook Integrations</CardTitle>
                </div>
                <CardDescription>
                  Receive HTTP POST callbacks for job events
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="space-y-0.5">
                    <div className="font-medium">Enable Webhook Notifications</div>
                    <div className="text-sm text-muted-foreground">
                      Send HTTP POST requests to your webhook URL
                    </div>
                  </div>
                  <Switch
                    checked={notifications.enable_webhook_notifications}
                    onCheckedChange={(checked) =>
                      setNotifications({
                        ...notifications,
                        enable_webhook_notifications: checked,
                      })
                    }
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Webhook URL
                  </label>
                  <Input
                    type="url"
                    placeholder="https://example.com/webhooks/bacowr"
                    value={notifications.webhook_url}
                    onChange={(e) =>
                      setNotifications({
                        ...notifications,
                        webhook_url: e.target.value,
                      })
                    }
                    disabled={!notifications.enable_webhook_notifications}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Your server endpoint for receiving webhook events
                  </p>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={handleTestWebhook}
                    disabled={
                      !notifications.enable_webhook_notifications ||
                      !notifications.webhook_url ||
                      testWebhookMutation.isPending
                    }
                  >
                    <Send className="h-4 w-4 mr-2" />
                    {testWebhookMutation.isPending ? 'Sending...' : 'Send Test Webhook'}
                  </Button>
                </div>

                {notifications.enable_webhook_notifications && notifications.webhook_url && (
                  <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                    <div className="flex gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-green-900 dark:text-green-100">
                        <strong>Webhook notifications active</strong>
                        <p className="text-green-700 dark:text-green-300 mt-1">
                          POST requests will be sent to <strong>{notifications.webhook_url}</strong> with HMAC signatures for verification.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="bg-muted rounded-lg p-3 text-sm space-y-2">
                  <div className="font-medium">Webhook Events:</div>
                  <ul className="list-disc list-inside text-muted-foreground space-y-1">
                    <li><code className="text-xs bg-background px-1 py-0.5 rounded">job.completed</code> - Job finished (delivered/blocked/aborted)</li>
                    <li><code className="text-xs bg-background px-1 py-0.5 rounded">job.error</code> - Job encountered an error</li>
                  </ul>
                  <p className="text-muted-foreground text-xs mt-2">
                    All webhooks include HMAC-SHA256 signatures in the <code className="bg-background px-1 py-0.5 rounded">X-BACOWR-Signature</code> header.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Save Button */}
            <Card>
              <CardContent className="pt-6">
                <Button
                  onClick={handleSaveNotifications}
                  className="w-full"
                  disabled={updateNotificationsMutation.isPending}
                >
                  <Save className="h-4 w-4 mr-2" />
                  {updateNotificationsMutation.isPending ? 'Saving...' : 'Save Notification Preferences'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
